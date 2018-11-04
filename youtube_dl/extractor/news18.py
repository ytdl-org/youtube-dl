from __future__ import unicode_literals

import re

from .common import InfoExtractor

class News18IE(InfoExtractor):
    _VALID_URL = r'''https?:\/\/www\.news18\.com[a-zA-Z0-9_\/-]+-(?P<id>\d+)\.html'''

    def _real_extract(self, url):
        IE_NAME = 'News18'
        video_id = self._match_id(url)
        webpage = self._download_webpage(url,video_id)
        video_url = self._search_regex(r'(?P<url>https?:\/\/vodpd\.news18\.com[\/\w_-]+\.mp4)', webpage, 'video URL',default='')
        title = self._og_search_title(webpage)

        return {
            'url': video_url,
            'id': video_id,
            'title': title,
            'ext': '.mp4'
        }

