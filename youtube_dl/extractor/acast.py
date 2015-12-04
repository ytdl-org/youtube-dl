# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..compat import compat_str
from ..utils import int_or_none


class ACastBaseIE(InfoExtractor):
    _API_BASE_URL = 'https://www.acast.com/api/'


class ACastIE(ACastBaseIE):
    IE_NAME = 'acast'
    _VALID_URL = r'https?://(?:www\.)?acast\.com/(?P<channel>[^/]+)/(?P<id>[^/#?]+)'
    _TEST = {
        'url': 'https://www.acast.com/gardenersquestiontime/liverpool',
        'md5': '9e9cd59c3a8a7d8d5407605f51093050',
        'info_dict': {
            'id': '43da2262-ade7-420c-8564-f6367da7c010',
            'ext': 'mp3',
            'title': 'Liverpool',
            'timestamp': 1446163200000,
            'description': 'md5:170432c9956eec0670d7080a75000d5b',
            'duration': 2520,
        }
    }

    def _real_extract(self, url):
        channel, display_id = re.match(self._VALID_URL, url).groups()
        cast_data = self._download_json(self._API_BASE_URL + 'channels/%s/acasts/%s/playback' % (channel, display_id), display_id)

        return {
            'id': compat_str(cast_data['id']),
            'display_id': display_id,
            'url': cast_data['blings'][0]['audio'],
            'title': cast_data['name'],
            'description': cast_data.get('description'),
            'thumbnail': cast_data.get('image'),
            'timestamp': int_or_none(cast_data.get('publishingDate')),
            'duration': int_or_none(cast_data.get('duration')),
        }


class ACastChannelIE(ACastBaseIE):
    IE_NAME = 'acast:channel'
    _VALID_URL = r'https?://(?:www\.)?acast\.com/(?P<id>[^/#?]+)'
    _TEST = {
        'url': 'https://www.acast.com/gardenersquestiontime',
        'info_dict': {
            'id': '9d8f6f73-6b9d-4d16-9399-52bf88f8f611',
            'title': 'Gardeners\' Question Time',
            'description': 'md5:c7ef18049da6a52b63d371b3edccce90',
        },
        'playlist_mincount': 5,
    }

    def _real_extract(self, url):
        display_id = self._match_id(url)
        channel_data = self._download_json(self._API_BASE_URL + 'channels/%s' % display_id, display_id)
        casts = self._download_json(self._API_BASE_URL + 'channels/%s/acasts' % display_id, display_id)
        entries = [self.url_result('https://www.acast.com/%s/%s' % (display_id, cast['url']), 'ACast') for cast in casts]

        return self.playlist_result(entries, compat_str(channel_data['id']), channel_data['name'], channel_data.get('description'))
