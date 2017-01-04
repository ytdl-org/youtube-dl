# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import clean_html


class ElibIE(InfoExtractor):
    _VALID_URL = r'https?://delivery.*\.elib\.se/Library/(?P<id>[^/#?]+)'

    _TEST = {
        # Fake ID, real IDs are loan-specific
        'url': 'https://delivery-32.elib.se/Library/123a4d5a-1e3a-2412-84ae-4a36134e0ac1',
        'only_matching': True,
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        data = self._download_json(
            'https://webservices.elib.se/librarystreaming/v1.0/streamdata/' + video_id,
            video_id, query={'format': 'json'})

        return {
            'id': video_id,
            'title': data['product']['title'],
            'url': data['streamUri'],
            'ext': 'mp3',
            'vcodec': 'none',
            'description': clean_html(data['product'].get('description')),
            'thumbnail': data['product'].get('coverImage'),
        }
