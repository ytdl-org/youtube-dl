import datetime
import json
import os
import re
import socket

from .common import InfoExtractor
from ..utils import (
    compat_http_client,
    compat_parse_qs,
    compat_str,
    compat_urllib_error,
    compat_urllib_parse_urlparse,
    compat_urllib_request,

    ExtractorError,
    unescapeHTML,
)


class BlipTVIE(InfoExtractor):
    """Information extractor for blip.tv"""

    _VALID_URL = r'^(?:https?://)?(?:\w+\.)?blip\.tv/((.+/)|(play/)|(api\.swf#))(.+)$'
    _URL_EXT = r'^.*\.([a-z0-9]+)$'
    IE_NAME = u'blip.tv'
    _TEST = {
        u'url': u'http://blip.tv/cbr/cbr-exclusive-gotham-city-imposters-bats-vs-jokerz-short-3-5796352',
        u'file': u'5779306.m4v',
        u'md5': u'80baf1ec5c3d2019037c1c707d676b9f',
        u'info_dict': {
            u"upload_date": u"20111205", 
            u"description": u"md5:9bc31f227219cde65e47eeec8d2dc596", 
            u"uploader": u"Comic Book Resources - CBR TV", 
            u"title": u"CBR EXCLUSIVE: \"Gotham City Imposters\" Bats VS Jokerz Short 3"
        }
    }

    def report_direct_download(self, title):
        """Report information extraction."""
        self.to_screen(u'%s: Direct download detected' % title)

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        if mobj is None:
            raise ExtractorError(u'Invalid URL: %s' % url)

        # See https://github.com/rg3/youtube-dl/issues/857
        api_mobj = re.match(r'http://a\.blip\.tv/api\.swf#(?P<video_id>[\d\w]+)', url)
        if api_mobj is not None:
            url = 'http://blip.tv/play/g_%s' % api_mobj.group('video_id')
        urlp = compat_urllib_parse_urlparse(url)
        if urlp.path.startswith('/play/'):
            request = compat_urllib_request.Request(url)
            response = compat_urllib_request.urlopen(request)
            redirecturl = response.geturl()
            rurlp = compat_urllib_parse_urlparse(redirecturl)
            file_id = compat_parse_qs(rurlp.fragment)['file'][0].rpartition('/')[2]
            url = 'http://blip.tv/a/a-' + file_id
            return self._real_extract(url)


        if '?' in url:
            cchar = '&'
        else:
            cchar = '?'
        json_url = url + cchar + 'skin=json&version=2&no_wrap=1'
        request = compat_urllib_request.Request(json_url)
        request.add_header('User-Agent', 'iTunes/10.6.1')
        self.report_extraction(mobj.group(1))
        info = None
        try:
            urlh = compat_urllib_request.urlopen(request)
            if urlh.headers.get('Content-Type', '').startswith('video/'): # Direct download
                basename = url.split('/')[-1]
                title,ext = os.path.splitext(basename)
                title = title.decode('UTF-8')
                ext = ext.replace('.', '')
                self.report_direct_download(title)
                info = {
                    'id': title,
                    'url': url,
                    'uploader': None,
                    'upload_date': None,
                    'title': title,
                    'ext': ext,
                    'urlhandle': urlh
                }
        except (compat_urllib_error.URLError, compat_http_client.HTTPException, socket.error) as err:
            raise ExtractorError(u'ERROR: unable to download video info webpage: %s' % compat_str(err))
        if info is None: # Regular URL
            try:
                json_code_bytes = urlh.read()
                json_code = json_code_bytes.decode('utf-8')
            except (compat_urllib_error.URLError, compat_http_client.HTTPException, socket.error) as err:
                raise ExtractorError(u'Unable to read video info webpage: %s' % compat_str(err))

            try:
                json_data = json.loads(json_code)
                if 'Post' in json_data:
                    data = json_data['Post']
                else:
                    data = json_data

                upload_date = datetime.datetime.strptime(data['datestamp'], '%m-%d-%y %H:%M%p').strftime('%Y%m%d')
                if 'additionalMedia' in data:
                    formats = sorted(data['additionalMedia'], key=lambda f: int(f['media_height']))
                    best_format = formats[-1]
                    video_url = best_format['url']
                else:
                    video_url = data['media']['url']
                umobj = re.match(self._URL_EXT, video_url)
                if umobj is None:
                    raise ValueError('Can not determine filename extension')
                ext = umobj.group(1)

                info = {
                    'id': compat_str(data['item_id']),
                    'url': video_url,
                    'uploader': data['display_name'],
                    'upload_date': upload_date,
                    'title': data['title'],
                    'ext': ext,
                    'format': data['media']['mimeType'],
                    'thumbnail': data['thumbnailUrl'],
                    'description': data['description'],
                    'player_url': data['embedUrl'],
                    'user_agent': 'iTunes/10.6.1',
                }
            except (ValueError,KeyError) as err:
                raise ExtractorError(u'Unable to parse video information: %s' % repr(err))

        return [info]


class BlipTVUserIE(InfoExtractor):
    """Information Extractor for blip.tv users."""

    _VALID_URL = r'(?:(?:(?:https?://)?(?:\w+\.)?blip\.tv/)|bliptvuser:)([^/]+)/*$'
    _PAGE_SIZE = 12
    IE_NAME = u'blip.tv:user'

    def _real_extract(self, url):
        # Extract username
        mobj = re.match(self._VALID_URL, url)
        if mobj is None:
            raise ExtractorError(u'Invalid URL: %s' % url)

        username = mobj.group(1)

        page_base = 'http://m.blip.tv/pr/show_get_full_episode_list?users_id=%s&lite=0&esi=1'

        page = self._download_webpage(url, username, u'Downloading user page')
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
            page = self._download_webpage(url, username,
                                          u'Downloading video ids from page %d' % pagenum)

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

        urls = [u'http://blip.tv/%s' % video_id for video_id in video_ids]
        url_entries = [self.url_result(vurl, 'BlipTV') for vurl in urls]
        return [self.playlist_result(url_entries, playlist_title = username)]
