# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor


class KeekIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?keek\.com/keek/(?P<id>\w+)'
    IE_NAME = 'keek'
    _TEST = {
        'url': 'https://www.keek.com/keek/NODfbab',
        'md5': '9b0636f8c0f7614afa4ea5e4c6e57e83',
        'info_dict': {
            'id': 'NODfbab',
            'ext': 'mp4',
            'title': 'test chars: "\'/\\ä<>This is a test video for youtube-dl.For more information, contact phihag@phihag.de . - Video - Videos on Keek',
            'description': 'md5:35d42050a3ece241d5ddd7fdcc6fd896',
            'uploader': 'ytdl',
            'uploader_id': 'eGT5bab',
        },
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)

        webpage = self._download_webpage(url, video_id)

        return {
            'id': video_id,
            'url': self._og_search_video_url(webpage),
            'ext': 'mp4',
            'title': self._og_search_title(webpage),
            'description': self._og_search_description(webpage),
            'thumbnail': self._og_search_thumbnail(webpage),
            'uploader': self._search_regex(r'data-username="([^"]+)"', webpage, 'uploader', fatal=False),
            'uploader_id': self._search_regex(r'data-user-id="([^"]+)"', webpage, 'uploader id', fatal=False),
        }
