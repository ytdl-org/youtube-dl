# encoding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import (
    clean_html
)


class RBMARadioIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?rbmaradio\.com/shows/[^/]+/episodes/(?P<id>[^/]+)$'
    _TEST = {
        'url': 'https://www.rbmaradio.com/shows/main-stage/episodes/ford-lopatin-live-at-primavera-sound-2011',
        'md5': '6bc6f9bcb18994b4c983bc3bf4384d95',
        'info_dict': {
            'id': 'ford-lopatin-live-at-primavera-sound-2011',
            'ext': 'mp3',
            'description': 'Joel Ford and Daniel ’Oneohtrix Point Never’ Lopatin fly their midified pop extravaganza to Spain. Live at Primavera Sound 2011.',
            'title': 'Ford & Lopatin - Main Stage',
        },
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)

        webpage = self._download_webpage(url, video_id)
        json_data = self._search_regex(r'<script>window\.__INITIAL_STATE__\s*=\s*(.+?)</script>',
                                       webpage, 'json data')
        data = self._parse_json(json_data, video_id)

        item = None
        for episode in data['episodes']:
            items = data['episodes'][episode]
            if video_id in items:
                item = items[video_id]

        video_url = item['audioURL'] + '?cbr=256'

        return {
            'id': video_id,
            'url': video_url,
            'title': item.get('title') + ' - ' + item.get('showTitle'),
            'description': clean_html(item.get('longTeaser')),
            'thumbnail': self._proto_relative_url(item.get('imageURL', {}).get('landscape')),
            'duration': item.get('duration'),
        }
