# encoding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor


class DumpIE(InfoExtractor):
    _VALID_URL = r'^https?://(?:www\.)?dump\.com/(?P<id>[a-zA-Z0-9]+)/'

    _TEST = {
        'url': 'http://www.dump.com/oneus/',
        'md5': 'ad71704d1e67dfd9e81e3e8b42d69d99',
        'info_dict': {
            'id': 'oneus',
            'ext': 'flv',
            'title': "He's one of us.",
            'thumbnail': 're:^https?://.*\.jpg$',
        },
    }

    def _real_extract(self, url):
        m = re.match(self._VALID_URL, url)
        video_id = m.group('id')

        webpage = self._download_webpage(url, video_id)
        video_url = self._search_regex(
            r's1.addVariable\("file",\s*"([^"]+)"', webpage, 'video URL')

        thumb = self._og_search_thumbnail(webpage)
        title = self._search_regex(r'<b>([^"]+)</b>', webpage, 'title')

        return {
            'id': video_id,
            'title': title,
            'url': video_url,
            'thumbnail': thumb,
        }
