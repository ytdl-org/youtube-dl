from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import parse_iso8601


class Abc7NewsIE(InfoExtractor):
    _VALID_URL = r'https?://abc7news\.com(?:/[^/]+/(?P<display_id>[^/]+))?/(?P<id>\d+)'
    _TESTS = [
        {
            'url': 'http://abc7news.com/entertainment/east-bay-museum-celebrates-vintage-synthesizers/472581/',
            'info_dict': {
                'id': '472581',
                'display_id': 'east-bay-museum-celebrates-vintage-synthesizers',
                'ext': 'mp4',
                'title': 'East Bay museum celebrates history of synthesized music',
                'description': 'md5:a4f10fb2f2a02565c1749d4adbab4b10',
                'thumbnail': 're:^https?://.*\.jpg$',
                'timestamp': 1421123075,
                'upload_date': '20150113',
                'uploader': 'Jonathan Bloom',
            },
            'params': {
                # m3u8 download
                'skip_download': True,
            },
        },
        {
            'url': 'http://abc7news.com/472581',
            'only_matching': True,
        },
    ]

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')
        display_id = mobj.group('display_id') or video_id

        webpage = self._download_webpage(url, display_id)

        m3u8 = self._html_search_meta(
            'contentURL', webpage, 'm3u8 url', fatal=True)

        formats = self._extract_m3u8_formats(m3u8, display_id, 'mp4')
        self._sort_formats(formats)

        title = self._og_search_title(webpage).strip()
        description = self._og_search_description(webpage).strip()
        thumbnail = self._og_search_thumbnail(webpage)
        timestamp = parse_iso8601(self._search_regex(
            r'<div class="meta">\s*<time class="timeago" datetime="([^"]+)">',
            webpage, 'upload date', fatal=False))
        uploader = self._search_regex(
            r'rel="author">([^<]+)</a>',
            webpage, 'uploader', default=None)

        return {
            'id': video_id,
            'display_id': display_id,
            'title': title,
            'description': description,
            'thumbnail': thumbnail,
            'timestamp': timestamp,
            'uploader': uploader,
            'formats': formats,
        }
