# coding: utf-8
from __future__ import unicode_literals

import re
import itertools

from .common import InfoExtractor
from ..utils import urlencode_postdata


class TwitCastingIE(InfoExtractor):
    _VALID_URL = r'https?://(?:[^/]+\.)?twitcasting\.tv/(?P<uploader_id>[^/]+)/movie/(?P<id>\d+)'
    _TESTS = [{
        'url': 'https://twitcasting.tv/ivetesangalo/movie/2357609',
        'md5': '745243cad58c4681dc752490f7540d7f',
        'info_dict': {
            'id': '2357609',
            'ext': 'mp4',
            'title': 'Live #2357609',
            'uploader_id': 'ivetesangalo',
            'description': "Moi! I'm live on TwitCasting from my iPhone.",
            'thumbnail': r're:^https?://.*\.jpg$',
        },
        'params': {
            'skip_download': True,
        },
    }, {
        'url': 'https://twitcasting.tv/mttbernardini/movie/3689740',
        'info_dict': {
            'id': '3689740',
            'ext': 'mp4',
            'title': 'Live playing something #3689740',
            'uploader_id': 'mttbernardini',
            'description': "I'm live on TwitCasting from my iPad. password: abc (Santa Marinella/Lazio, Italia)",
            'thumbnail': r're:^https?://.*\.jpg$',
        },
        'params': {
            'skip_download': True,
            'videopassword': 'abc',
        },
    }]

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')
        uploader_id = mobj.group('uploader_id')

        video_password = self._downloader.params.get('videopassword')
        request_data = None
        if video_password:
            request_data = urlencode_postdata({
                'password': video_password,
            })
        webpage = self._download_webpage(url, video_id, data=request_data)

        title = (self._html_search_regex(
            r'(?s)<[^>]+id=["\']movietitle[^>]+>(.+?)</',
            webpage, 'title', default=None)
            or self._html_search_meta('twitter:title', webpage, fatal=True))
        # title is split across lines with lots of whitespace
        title = title.replace('\n', ' ')
        while '  ' in title:
            title = title.replace('  ', ' ')

        m3u8_url = self._search_regex(
            (r'data-movie-url=(["\'])(?P<url>(?:(?!\1).)+)\1',
             r'(["\'])(?P<url>http.+?\.m3u8.*?)\1'),
            webpage, 'm3u8 url', group='url')
        m3u8_url = m3u8_url.replace('\\/', '/')
        formats = self._extract_m3u8_formats(
            m3u8_url, video_id, ext='mp4', entry_protocol='m3u8_native',
            m3u8_id='hls')

        thumbnail = self._og_search_thumbnail(webpage)
        description = self._og_search_description(
            webpage, default=None) or self._html_search_meta(
            'twitter:description', webpage)

        return {
            'id': video_id,
            'title': title,
            'description': description,
            'thumbnail': thumbnail,
            'uploader_id': uploader_id,
            'formats': formats,
        }


class TwitCastingHistoryIE(InfoExtractor):
    _VALID_URL = r'https?://(?:[^/]+\.)?twitcasting\.tv/(?P<uploader_id>[^/]+)/show'
    _TESTS = [
        {
            'url': 'https://twitcasting.tv/mttbernardini/show/',
            'info_dict': {
                'title': 'Matteo Bernardini',
                'id': 'mttbernardini',
            },
            'playlist_count': 1,
        },
    ]

    def _get_meta_and_entries(self, url):
        for page_num in itertools.count(0):
            page_url = "%s/%s" % (url.rstrip('/'), page_num)
            pagenum = None
            list_id = None
            webpage = self._download_webpage(
                page_url, list_id,
                'Downloading page %s' % pagenum)

            if page_num == 0:
                title = self._search_regex(
                    r'(?s)<[^>]+class=["\']tw-user-nav-name[^>]+>(.+?)</',
                    webpage, 'playlist_title', fatal=False)

                if title is not None:
                    title = title.strip()

                user_id = self._search_regex(
                    r'data-user-id=["\'](.+?)["\']',
                    webpage, 'user_id', fatal=False)
                if user_id is not None:
                    user_id = user_id.strip()

                yield (title, user_id)

            first_page_selected = webpage.find('class="selected">1</a>') != -1
            if page_num != 0 and first_page_selected:
                break

            matches = re.finditer(r'''<a[^>]+class=["']tw-movie-thumbnail["'][^>]+href="(.+)"[^>]+>((?:\n|.)*?)</a>''', webpage)
            matches = list(matches)

            for match in matches:
                href = match.group(1)
                inner = match.group(2)
                # if REC isn't present either a live broadcast or an image
                # e.g. https://twitcasting.tv/marrynontan/movie/506296434
                if 'REC' not in inner:
                    continue

                # skip videos that require a password
                # e.g. https://twitcasting.tv/mttbernardini/movie/3689740
                locked = re.search(r'''src="/img/locked.png"''', inner)
                if locked is not None:
                    continue

                title = self._search_regex(
                    r'''<[^>]+class=["']tw-movie-thumbnail-title[^>]+>[ \n]*?(.+?) *?</''',
                    inner, 'title', fatal=False)
                if title is not None:
                    title = title.strip()

                video_url = 'https://twitcasting.tv%s' % href
                video_id = href.split('/')[-1]
                result = self.url_result(video_url,
                    ie=TwitCastingIE.ie_key(), video_id=video_id, video_title=title)
                yield result

    def _real_extract(self, url):
        entries = self._get_meta_and_entries(url)

        (title, user_id) = next(entries)

        result = self.playlist_result(entries, playlist_title=title, playlist_id=user_id)

        return result
