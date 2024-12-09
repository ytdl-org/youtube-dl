# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    extract_attributes,
    int_or_none,
    traverse_obj
)
import json
import re

class CanalrcnIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?canalrcn\.com/(?:[^/]+/)+(?P<id>[^/?&#]+)'
    _TESTS = [{
        'url': 'https://www.canalrcn.com/la-rosa-de-guadalupe/capitulos/la-rosa-de-guadalupe-capitulo-58-los-enamorados-3619',
        'info_dict': {
            'id': 'x8ecrn2',
            'ext': 'mp4',
            'title': 'La rosa de Guadalupe | Capítulo 58 | Los enamorados',
            'description': 'Pamela conoce a un hombre, pero sus papás no se lo aprueban porque no tiene recursos.',
            'thumbnail': r're:^https?://.*\.(?:jpg|png|webp)',
        },
        'params': {
            'skip_download': True,
        },
        'skip': 'Geo-restricted to Colombia',
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)
        
        # Extract JSON-LD data
        json_ld = self._search_regex(
            r'<script[^>]+type=(["\'])application/ld\+json\1[^>]*>(?P<json>[^<]+)</script>',
            webpage, 'JSON-LD', group='json', default='{}')
        
        try:
            json_data = json.loads(json_ld)
        except json.JSONDecodeError:
            raise ExtractorError('Could not parse JSON-LD data')
            
        # Find the VideoObject in the JSON-LD array
        video_data = None
        if isinstance(json_data, list):
            for item in json_data:
                if isinstance(item, dict) and item.get('@type') == 'VideoObject':
                    video_data = item
                    break
        
        if not video_data:
            raise ExtractorError('Could not find video information in JSON-LD data')

        # Extract player information
        player_match = re.search(r'dailymotion\.createPlayer\("([^"]+)",\s*{([^}]+)}', webpage)
        if not player_match:
            raise ExtractorError('Could not find player configuration')

        player_config = player_match.group(2)
        video_url_match = re.search(r'video:\s*["\']([^"\']+)', player_config)
        if not video_url_match:
            raise ExtractorError('Could not find video URL')

        dailymotion_id = video_url_match.group(1).split('&&')[0]

        # Configure geo-bypass headers
        self._downloader.params['geo_verification_proxy'] = 'co'

        return {
            '_type': 'url_transparent',
            'url': 'http://www.dailymotion.com/video/%s' % dailymotion_id,
            'ie_key': 'Dailymotion',
            'id': dailymotion_id,
            'title': video_data.get('name'),
            'description': video_data.get('description'),
            'thumbnail': video_data.get('thumbnailUrl'),
            'duration': video_data.get('duration'),
            'note': 'Video is geo-restricted to Colombia',
        }