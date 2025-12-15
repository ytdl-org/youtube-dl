# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import (
    try_get,
    url_or_none,
    parse_iso8601,
)
from ..compat import compat_str


class LivestreamfailsIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?livestreamfails\.com/clip/(?P<id>[0-9]+)'
    _TESTS = [{
        'url': 'https://livestreamfails.com/clip/139200',
        'md5': '8a03aea1a46e94a05af6410337463102',
        'info_dict': {
            'id': '139200',
            'ext': 'mp4',
            'display_id': 'ConcernedLitigiousSalmonPeteZaroll-O8yo9W2L8OZEKhV2',
            'title': 'Streamer jumps off a trampoline at full speed',
            'creator': 'paradeev1ch',
            'thumbnail': 'https://livestreamfails-image-prod.b-cdn.net/image/3877b1d38db083fa25c82685bbaf645637e575ea.png',
            'timestamp': 1656271785,
            'upload_date': '20220626',
        }
    }]

    def _real_extract(self, url):
        id = self._match_id(url)

        # https://livestreamfails.com/clip/id uses https://api.livestreamfails.com/clip/ to fetch the video metadata
        # Use the same endpoint here to avoid loading and parsing the provided page (which requires JS)
        api_response = self._download_json('https://api.livestreamfails.com/clip/' + id, id)

        video_url = 'https://livestreamfails-video-prod.b-cdn.net/video/' + api_response['videoId']
        title = api_response['label']

        return {
            'id': id,
            'url': video_url,
            'title': title,
            'display_id': api_response.get('sourceId'),  # Twitch ID of clip
            'timestamp': parse_iso8601(api_response.get('createdAt')),
            'creator': try_get(api_response, lambda x: x['streamer']['label'], compat_str),
            'thumbnail': url_or_none(try_get(api_response, lambda x: 'https://livestreamfails-image-prod.b-cdn.net/image/' + x['imageId']))
        }
