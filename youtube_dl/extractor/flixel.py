# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor


class FlixelIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?flixel\.com/cinemagraph/(?P<id>[0-9a-zA-Z]+)'
    _TEST = {
        'url': 'https://flixel.com/cinemagraph/tg64m4fmxbqu5yrywoz5/',
        'md5': '374a8a8f8902f7db0f4a8d6f580c23ed',
        'info_dict': {
            'id': 'tg64m4fmxbqu5yrywoz5',
            'ext': 'mp4',
            'title': 'ROSSIO',
            'uploader': 'capn',
            'duration': 3.575,
            'thumbnail': 'https://cdn.flixel.com/flixel/tg64m4fmxbqu5yrywoz5.thumbnail.jpg?v=1',
            'webpage_url': 'https://flixel.com/cinemagraph/tg64m4fmxbqu5yrywoz5/',
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        json_url = 'https://api.flixel.com/2/flixels/{0}'.format(video_id)
        meta = self._download_json(json_url, video_id)
        return {
            'id': video_id,
            'title': meta.get('caption'),
            'url': meta.get('hd_mp4'),
            'uploader': meta.get('username'),
            'duration': meta.get('duration'),
            'thumbnail': meta.get('thumbnail'),
            'webpage_url': meta.get('link'),
        }
