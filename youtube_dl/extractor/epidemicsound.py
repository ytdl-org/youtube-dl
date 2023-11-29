# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    float_or_none,
    txt_or_none,
    unified_timestamp,
    url_or_none,
    traverse_obj,
    str_or_none,
    T,
)


class EpidemicSoundIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?epidemicsound\.com/track/(?P<id>[0-9a-zA-Z]+)'
    _TESTS = [{
        'url': 'https://www.epidemicsound.com/track/yFfQVRpSPz/',
        'md5': 'd98ff2ddb49e8acab9716541cbc9dfac',
        'info_dict': {
            'id': 'yFfQVRpSPz',
            'ext': 'mp3',
            'tags': ['foley', 'door', 'knock', 'glass', 'window', 'glass door knock'],
            'title': 'Door Knock Door 1',
            'duration': 1,
            'thumbnail': 'https://cdn.epidemicsound.com/curation-assets/commercial-release-cover-images/default-sfx/3000x3000.jpg',
            'timestamp': 1415320353,
            'upload_date': '20141107',
        }
    },
        {
            'url': 'https://www.epidemicsound.com/track/mj8GTTwsZd/',
            'md5': 'c82b745890f9baf18dc2f8d568ee3830',
            'info_dict': {
                'id': 'mj8GTTwsZd',
                'ext': 'mp3',
                'tags': ["liquid drum n bass", "energetic"],
                'title': 'Noplace',
                'duration': 237,
                'thumbnail': 'https://cdn.epidemicsound.com/curation-assets/commercial-release-cover-images/11138/3000x3000.jpg',
                'timestamp': 1694426482,
                'upload_date': '20230911',
            }
        },
    ]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        json_data = self._download_json('https://www.epidemicsound.com/json/track/' + video_id, video_id)

        if not traverse_obj(json_data, ('stems', Ellipsis)):
            raise ExtractorError('No downloadable content found')

        formats = list(reversed([
            {
                'format_id': str_or_none(key),
                'url': url_or_none(value.get('lqMp3Url'))
            } for key, value in json_data.get('stems').items()
        ]))

        for f in formats:
            for key, value in f.items():
                if value is None or key is None:
                    del f

        if len(formats) == 0:
            raise ExtractorError('No downloadable content found')

        info = traverse_obj(json_data, {
            'tags': ('metadataTags', Ellipsis, T(txt_or_none)),
            'title': ('title', T(txt_or_none)),
            'duration': ('length', T(float_or_none)),
            'timestamp': ('added', T(unified_timestamp)),
            'thumbnail': ('imageUrl', T(url_or_none))})

        info['id'] = video_id
        info['formats'] = formats

        if not info.get('tags'):
            del info['tags']

        if not info.get('title'):
            raise ExtractorError('No title found')

        return info
