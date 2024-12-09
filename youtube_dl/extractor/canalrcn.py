# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    clean_html,
    try_get,
)
import json

class CanalrcnIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?canalrcn\.com/(?:[^/]+/)+(?P<id>[^/?&#]+)'
    
    # Specify geo-restriction
    _GEO_COUNTRIES = ['CO']
    
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
        'expected_warnings': ['Video is geo-restricted to Colombia'],
        'skip': 'Geo-restricted to Colombia'
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)
        
        json_ld = self._search_regex(
            r'<script[^>]+type=(["\'])application/ld\+json\1[^>]*>(?P<json>[^<]+)</script>',
            webpage, 'JSON-LD', group='json', default='{}')
        
        try:
            json_data = json.loads(json_ld)
        except json.JSONDecodeError:
            raise ExtractorError('Could not parse JSON-LD data')
            
        video_data = None
        if isinstance(json_data, list):
            for item in json_data:
                if isinstance(item, dict) and item.get('@type') == 'VideoObject':
                    video_data = item
                    break
        
        if not video_data:
            raise ExtractorError('Could not find video information in JSON-LD data')

        embed_url = video_data.get('embedUrl')
        if not embed_url:
            raise ExtractorError('Could not find video embed URL')

        dailymotion_id = self._search_regex(
            r'dailymotion\.com/(?:embed/)?video/([a-zA-Z0-9]+)',
            embed_url,
            'dailymotion id'
        )
        
        #geo-restriction handling
        self.raise_geo_restricted(
            msg='This video is only available in Colombia',
            countries=self._GEO_COUNTRIES
        )

        return {
            '_type': 'url_transparent',
            'url': 'http://www.dailymotion.com/video/%s' % dailymotion_id,
            'ie_key': 'Dailymotion',
            'id': dailymotion_id,
            'title': video_data.get('name'),
            'description': video_data.get('description'),
            'thumbnail': video_data.get('thumbnailUrl'),
            'duration': video_data.get('duration'),
        }