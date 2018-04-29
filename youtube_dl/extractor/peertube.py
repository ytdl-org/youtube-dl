# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor


class PeertubeIE(InfoExtractor):
    _BASE_VIDEO_URL = 'https://peertube.touhoppai.moe/static/webseed/%s-1080.mp4'
    _BASE_THUMBNAIL_URL = 'https://peertube.touhoppai.moe/static/previews/%s.jpg'
    IE_DESC = 'Peertube Videos'
    IE_NAME = 'Peertube'
    _VALID_URL = r'https?:\/\/peertube\.touhoppai\.moe\/videos\/watch\/(?P<id>[0-9|\-|a-z]+)'
    _TEST = {
        'url': 'https://peertube.touhoppai.moe/videos/watch/7f3421ae-6161-4a4a-ae38-d167aec51683',
        'md5': 'a5e1e4a978e6b789553198d1739f5643',
        'info_dict': {
            'id': '7f3421ae-6161-4a4a-ae38-d167aec51683',
            'ext': 'mp4',
            'title': 'David Revoy Live Stream: Speedpainting',
            'description': 'md5:5c09a6e3fdb5f56edce289d69fbe7567',
            'thumbnail': 'https://peertube.touhoppai.moe/static/previews/7f3421ae-6161-4a4a-ae38-d167aec51683.jpg',
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)
        title = self._og_search_title(webpage)
        return {
            'id': video_id,
            'title': title,
            'description': self._og_search_description(webpage),
            'url': self._BASE_VIDEO_URL % video_id,
            'thumbnail': self._BASE_THUMBNAIL_URL % video_id
        }
