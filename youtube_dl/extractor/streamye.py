# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor


class StreamYEIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?streamye\.com/(?P<id>[a-zA-Z0-9]+)'
    _TEST = {
        'url': 'https://streamye.com/vYbcQ2H',
        'info_dict': {
            'id': '7bb3fb92faca2ff47a64964637cda2fd',
            'ext': 'm4a',
            'title': '7bb3fb92faca2ff47a64964637cda2fd',
        },
        'params': {
            'format': 'bestvideo,bestaudio',
            'skip_download': True
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)
        video_url = self._html_search_regex(
            r'<iframe[^>]+src=([\'"])(?P<url>[^\'"]+)\1',
            webpage, 'url', group="url"
        )

        return self.url_result(video_url, ie="Generic")
