# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import (
    float_or_none,
    T,
    traverse_obj,
    txt_or_none,
    unified_timestamp,
    url_or_none,
)


class EpidemicSoundIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?epidemicsound\.com/track/(?P<id>[0-9a-zA-Z]+)'
    _TESTS = [{
        'url': 'https://www.epidemicsound.com/track/yFfQVRpSPz/',
        'md5': 'd98ff2ddb49e8acab9716541cbc9dfac',
        'info_dict': {
            'id': '45014',
            'display_id': 'yFfQVRpSPz',
            'ext': 'mp3',
            'tags': ['foley', 'door', 'knock', 'glass', 'window', 'glass door knock'],
            'title': 'Door Knock Door 1',
            'duration': 1,
            'thumbnail': 'https://cdn.epidemicsound.com/curation-assets/commercial-release-cover-images/default-sfx/3000x3000.jpg',
            'timestamp': 1415320353,
            'upload_date': '20141107',
            'age_limit': None,
            # check that the "best" format was found, since test file MD5 doesn't
            # distinguish the formats
            'format': 'full',
        },
    }, {
        'url': 'https://www.epidemicsound.com/track/mj8GTTwsZd/',
        'md5': 'c82b745890f9baf18dc2f8d568ee3830',
        'info_dict': {
            'id': '148700',
            'display_id': 'mj8GTTwsZd',
            'ext': 'mp3',
            'tags': ['liquid drum n bass', 'energetic'],
            'title': 'Noplace',
            'duration': 237,
            'thumbnail': 'https://cdn.epidemicsound.com/curation-assets/commercial-release-cover-images/11138/3000x3000.jpg',
            'timestamp': 1694426482,
            'release_timestamp': 1700535606,
            'upload_date': '20230911',
            'age_limit': None,
            'format': 'full',
        },
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        json_data = self._download_json('https://www.epidemicsound.com/json/track/' + video_id, video_id)

        def fmt_or_none(f):
            if not f.get('format'):
                f['format'] = f.get('format_id')
            elif not f.get('format_id'):
                f['format_id'] = f['format']
            if not (f['url'] and f['format']):
                return
            if f.get('format_note'):
                f['format_note'] = 'track ID ' + f['format_note']
            f['preference'] = -1 if f['format'] == 'full' else -2
            return f

        formats = traverse_obj(json_data, (
            'stems', T(dict.items), Ellipsis, {
                'format': (0, T(txt_or_none)),
                'format_note': (1, 's3TrackId', T(txt_or_none)),
                'format_id': (1, 'stemType', T(txt_or_none)),
                'url': (1, 'lqMp3Url', T(url_or_none)),
            }, T(fmt_or_none)))

        self._sort_formats(formats)

        info = traverse_obj(json_data, {
            'id': ('id', T(txt_or_none)),
            'tags': ('metadataTags', Ellipsis, T(txt_or_none)),
            'title': ('title', T(txt_or_none)),
            'duration': ('length', T(float_or_none)),
            'timestamp': ('added', T(unified_timestamp)),
            'thumbnail': (('imageUrl', 'cover'), T(url_or_none)),
            'age_limit': ('isExplicit', T(lambda b: 18 if b else None)),
            'release_timestamp': ('releaseDate', T(unified_timestamp)),
        }, get_all=False)

        info.update(traverse_obj(json_data, {
            'categories': ('genres', Ellipsis, 'tag', T(txt_or_none)),
            'tags': ('metadataTags', Ellipsis, T(txt_or_none)),
        }))

        info.update({
            'display_id': video_id,
            'formats': formats,
        })

        return info
