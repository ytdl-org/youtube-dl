from __future__ import unicode_literals

import datetime
import re

from .common import InfoExtractor
from .subtitles import SubtitlesInfoExtractor
from ..utils import (
    compat_str,
    compat_urllib_request,

    unescapeHTML,
)


class BlipTVIE(SubtitlesInfoExtractor):
    """Information extractor for blip.tv"""

    _VALID_URL = r'https?://(?:\w+\.)?blip\.tv/((.+/)|(play/)|(api\.swf#))(?P<presumptive_id>.+)$'

    _TESTS = [{
        'url': 'http://blip.tv/cbr/cbr-exclusive-gotham-city-imposters-bats-vs-jokerz-short-3-5796352',
        'md5': 'c6934ad0b6acf2bd920720ec888eb812',
        'info_dict': {
            'id': '5779306',
            'ext': 'mov',
            'upload_date': '20111205',
            'description': 'md5:9bc31f227219cde65e47eeec8d2dc596',
            'uploader': 'Comic Book Resources - CBR TV',
            'title': 'CBR EXCLUSIVE: "Gotham City Imposters" Bats VS Jokerz Short 3',
        }
    }, {
        # https://github.com/rg3/youtube-dl/pull/2274
        'note': 'Video with subtitles',
        'url': 'http://blip.tv/play/h6Uag5OEVgI.html',
        'md5': '309f9d25b820b086ca163ffac8031806',
        'info_dict': {
            'id': '6586561',
            'ext': 'mp4',
            'uploader': 'Red vs. Blue',
            'description': 'One-Zero-One',
            'upload_date': '20130614',
            'title': 'Red vs. Blue Season 11 Episode 1',
        }
    }]

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        presumptive_id = mobj.group('presumptive_id')

        # See https://github.com/rg3/youtube-dl/issues/857
        embed_mobj = re.match(r'https?://(?:\w+\.)?blip\.tv/(?:play/|api\.swf#)([a-zA-Z0-9]+)', url)
        if embed_mobj:
            info_url = 'http://blip.tv/play/%s.x?p=1' % embed_mobj.group(1)
            info_page = self._download_webpage(info_url, embed_mobj.group(1))
            video_id = self._search_regex(
                r'data-episode-id="([0-9]+)', info_page, 'video_id')
            return self.url_result('http://blip.tv/a/a-' + video_id, 'BlipTV')
        
        cchar = '&' if '?' in url else '?'
        json_url = url + cchar + 'skin=json&version=2&no_wrap=1'
        request = compat_urllib_request.Request(json_url)
        request.add_header('User-Agent', 'iTunes/10.6.1')

        json_data = self._download_json(request, video_id=presumptive_id)

        if 'Post' in json_data:
            data = json_data['Post']
        else:
            data = json_data

        video_id = compat_str(data['item_id'])
        upload_date = datetime.datetime.strptime(data['datestamp'], '%m-%d-%y %H:%M%p').strftime('%Y%m%d')
        subtitles = {}
        formats = []
        if 'additionalMedia' in data:
            for f in data['additionalMedia']:
                if f.get('file_type_srt') == 1:
                    LANGS = {
                        'english': 'en',
                    }
                    lang = f['role'].rpartition('-')[-1].strip().lower()
                    langcode = LANGS.get(lang, lang)
                    subtitles[langcode] = f['url']
                    continue
                if not int(f['media_width']):  # filter m3u8
                    continue
                formats.append({
                    'url': f['url'],
                    'format_id': f['role'],
                    'width': int(f['media_width']),
                    'height': int(f['media_height']),
                })
        else:
            formats.append({
                'url': data['media']['url'],
                'width': int(data['media']['width']),
                'height': int(data['media']['height']),
            })
        self._sort_formats(formats)

        # subtitles
        video_subtitles = self.extract_subtitles(video_id, subtitles)
        if self._downloader.params.get('listsubtitles', False):
            self._list_available_subtitles(video_id, subtitles)
            return

        return {
            'id': video_id,
            'uploader': data['display_name'],
            'upload_date': upload_date,
            'title': data['title'],
            'thumbnail': data['thumbnailUrl'],
            'description': data['description'],
            'user_agent': 'iTunes/10.6.1',
            'formats': formats,
            'subtitles': video_subtitles,
        }

    def _download_subtitle_url(self, sub_lang, url):
        # For some weird reason, blip.tv serves a video instead of subtitles
        # when we request with a common UA
        req = compat_urllib_request.Request(url)
        req.add_header('Youtubedl-user-agent', 'youtube-dl')
        return self._download_webpage(req, None, note=False)


class BlipTVUserIE(InfoExtractor):
    _VALID_URL = r'(?:(?:(?:https?://)?(?:\w+\.)?blip\.tv/)|bliptvuser:)([^/]+)/*$'
    _PAGE_SIZE = 12
    IE_NAME = 'blip.tv:user'

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        username = mobj.group(1)

        page_base = 'http://m.blip.tv/pr/show_get_full_episode_list?users_id=%s&lite=0&esi=1'

        page = self._download_webpage(url, username, 'Downloading user page')
        mobj = re.search(r'data-users-id="([^"]+)"', page)
        page_base = page_base % mobj.group(1)

        # Download video ids using BlipTV Ajax calls. Result size per
        # query is limited (currently to 12 videos) so we need to query
        # page by page until there are no video ids - it means we got
        # all of them.

        video_ids = []
        pagenum = 1

        while True:
            url = page_base + "&page=" + str(pagenum)
            page = self._download_webpage(
                url, username, 'Downloading video ids from page %d' % pagenum)

            # Extract video identifiers
            ids_in_page = []

            for mobj in re.finditer(r'href="/([^"]+)"', page):
                if mobj.group(1) not in ids_in_page:
                    ids_in_page.append(unescapeHTML(mobj.group(1)))

            video_ids.extend(ids_in_page)

            # A little optimization - if current page is not
            # "full", ie. does not contain PAGE_SIZE video ids then
            # we can assume that this page is the last one - there
            # are no more ids on further pages - no need to query
            # again.

            if len(ids_in_page) < self._PAGE_SIZE:
                break

            pagenum += 1

        urls = ['http://blip.tv/%s' % video_id for video_id in video_ids]
        url_entries = [self.url_result(vurl, 'BlipTV') for vurl in urls]
        return [self.playlist_result(url_entries, playlist_title=username)]
