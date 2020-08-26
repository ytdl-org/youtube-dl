from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import (
    dict_get,
    float_or_none,
    int_or_none,
    unified_timestamp,
    update_url_query,
    url_or_none,
)


class TruNewsIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?trunews\.com/stream/(?P<id>[^/?#&]+)'
    _TEST = {
        'url': 'https://www.trunews.com/stream/will-democrats-stage-a-circus-during-president-trump-s-state-of-the-union-speech',
        'md5': 'a19c024c3906ff954fac9b96ce66bb08',
        'info_dict': {
            'id': '5c5a21e65d3c196e1c0020cc',
            'display_id': 'will-democrats-stage-a-circus-during-president-trump-s-state-of-the-union-speech',
            'ext': 'mp4',
            'title': "Will Democrats Stage a Circus During President Trump's State of the Union Speech?",
            'description': 'md5:c583b72147cc92cf21f56a31aff7a670',
            'duration': 3685,
            'timestamp': 1549411440,
            'upload_date': '20190206',
        },
        'add_ie': ['Zype'],
    }

    def _real_extract(self, url):
        display_id = self._match_id(url)

        video = self._download_json(
            'https://api.zype.com/videos', display_id, query={
                'app_key': 'PUVKp9WgGUb3-JUw6EqafLx8tFVP6VKZTWbUOR-HOm__g4fNDt1bCsm_LgYf_k9H',
                'per_page': 1,
                'active': 'true',
                'friendly_title': display_id,
            })['response'][0]

        zype_id = video['_id']

        thumbnails = []
        thumbnails_list = video.get('thumbnails')
        if isinstance(thumbnails_list, list):
            for thumbnail in thumbnails_list:
                if not isinstance(thumbnail, dict):
                    continue
                thumbnail_url = url_or_none(thumbnail.get('url'))
                if not thumbnail_url:
                    continue
                thumbnails.append({
                    'url': thumbnail_url,
                    'width': int_or_none(thumbnail.get('width')),
                    'height': int_or_none(thumbnail.get('height')),
                })

        return {
            '_type': 'url_transparent',
            'url': update_url_query(
                'https://player.zype.com/embed/%s.js' % zype_id,
                {'api_key': 'X5XnahkjCwJrT_l5zUqypnaLEObotyvtUKJWWlONxDoHVjP8vqxlArLV8llxMbyt'}),
            'ie_key': 'Zype',
            'id': zype_id,
            'display_id': display_id,
            'title': video.get('title'),
            'description': dict_get(video, ('description', 'ott_description', 'short_description')),
            'duration': int_or_none(video.get('duration')),
            'timestamp': unified_timestamp(video.get('published_at')),
            'average_rating': float_or_none(video.get('rating')),
            'view_count': int_or_none(video.get('request_count')),
            'thumbnails': thumbnails,
        }
