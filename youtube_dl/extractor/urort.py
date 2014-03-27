# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    compat_urllib_parse,
    unified_strdate,
)


class UrortIE(InfoExtractor):
    IE_DESC = 'NRK P3 Urørt'
    _VALID_URL = r'https?://(?:www\.)?urort\.p3\.no/#!/Band/(?P<id>[^/]+)$'

    _TEST = {
        'url': 'https://urort.p3.no/#!/Band/Gerilja',
        'md5': '5ed31a924be8a05e47812678a86e127b',
        'info_dict': {
            'id': '33124-4',
            'ext': 'mp3',
            'title': 'The Bomb',
            'thumbnail': 're:^https?://.+\.jpg',
            'like_count': int,
            'uploader': 'Gerilja',
            'uploader_id': 'Gerilja',
            'upload_date': '20100323',
        },
        'params': {
            'matchtitle': '^The Bomb$',  # To test, we want just one video
        }
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        playlist_id = mobj.group('id')

        fstr = compat_urllib_parse.quote("InternalBandUrl eq '%s'" % playlist_id)
        json_url = 'http://urort.p3.no/breeze/urort/TrackDtos?$filter=' + fstr
        songs = self._download_json(json_url, playlist_id)
        print(songs[0])

        entries = [{
            'id': '%d-%s' % (s['BandId'], s['$id']),
            'title': s['Title'],
            'url': s['TrackUrl'],
            'ext': 'mp3',
            'uploader_id': playlist_id,
            'uploader': s.get('BandName', playlist_id),
            'like_count': s.get('LikeCount'),
            'thumbnail': 'http://urort.p3.no/cloud/images/%s' % s['Image'],
            'upload_date': unified_strdate(s.get('Released')),
        } for s in songs]

        return {
            '_type': 'playlist',
            'id': playlist_id,
            'title': playlist_id,
            'entries': entries,
        }
