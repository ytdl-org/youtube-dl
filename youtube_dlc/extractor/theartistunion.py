# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import determine_ext, unified_timestamp


class TheArtistUnionIE(InfoExtractor):
    _VALID_URL = r'https://theartistunion.com/tracks/([0-9a-f]{6})'
    _TEST = {
        'url': 'https://theartistunion.com/tracks/f12c01',
        'md5': 'b8e48aa5aec70c46f7a5493f51559c8c',
        'info_dict': {
            'id': 'f12c01',
            'ext': 'mp3',
            'title': "The Grand Sound pres. 'Night Drive' - Relaxing Deep House & Progressive House Mix",
            'thumbnail': 'https://d2tml28x3t0b85.cloudfront.net/tracks/audio/original_artwork/da2fdc80248911e99afa516bbf6a0ff9/df4dd410248911e992f02f67adc0a722.jpg',
            'uploader': 'The Grand Sound',
            'uploader_id': 'thegrandsound',
            'uploader_url': 'https://theartistunion.com/thegrandsound',
            'timestamp': 1549044071,
            'upload_date': '20190201',
            'formats': [{
                'url': 'https://content.theartistunion.com/tracks/audio/stream_encode/da2fdc80248911e99afa516bbf6a0ff9/The-Grand-Sound-pres.-_Night-Drive_---Relaxing-Deep-House-_-Progressive-House-Mix.mp3',
                'format_id': 'stream_encode',
                'priority': -2,
            }, {
                'url': 'https://content.theartistunion.com/tracks/audio/:original/da2fdc80248911e99afa516bbf6a0ff9/The-Grand-Sound-pres.-_Night-Drive_---Relaxing-Deep-House-_-Progressive-House-Mix.mp3',
                'format_id': 'original',
            }],
        }
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        track_id = mobj.group(1)
        orig_info = self._download_json(
            'https://theartistunion.com/api/v3/tracks/{}.json'.format(track_id),
            track_id)

        # not using safe methods of getting info from the dict because this field is required
        info = {
            'id': track_id,
            'ext': determine_ext(orig_info['audio_source']),
        }

        info['formats'] = [{
            'url': orig_info['audio_source'],
            'format_id': 'stream_encode',
            'priority': -2,
        }, {
            'url': orig_info['audio_source'].replace('/tracks/audio/stream_encode/', '/tracks/audio/:original/'),
            'format_id': 'original',
        }]

        for source, dest in [
            ('original_artwork', 'thumbnail'),
            ('artist_name', 'uploader'),
            ('artist_username', 'uploader_id'),
            ('title', 'title'),
        ]:
            try:
                info[dest] = orig_info[source]
            except KeyError:
                pass

        try:
            info['uploader_url'] = 'https://theartistunion.com/' + orig_info['artist_username']
        except KeyError:
            pass

        try:
            info['timestamp'] = unified_timestamp(orig_info['published_at'])
        except KeyError:
            pass

        return info
