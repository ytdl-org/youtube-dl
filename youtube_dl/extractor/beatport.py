# coding: utf-8
from __future__ import unicode_literals

from youtube_dl.utils import int_or_none

from .common import ExtractorError, InfoExtractor


class BeatportIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?beatport\.com/(?P<uploader_id>\w+)/tracks/(?P<id>.+)/(?P<display_id>.+)'
    _TESTS = [{
        'url': 'https://www.beatport.com/musicalfreedom/tracks/l2axnqcd6azu/secrets-feat-vassy-original-mix',
        'md5': '11e330f6236be07f61fcc4669e972cd8',
        'info_dict': {
            'id': 'l2axnqcd6azu',
            'display_id': 'secrets-feat-vassy-original-mix',
            'uploader': 'Musical Freedom',
            'uploader_id': 'musicalfreedom',
            'uploader_url': 'http://www.musicalfreedom.com',
            'ext': 'mp4',
            'title': 'Secrets feat. Vassy',
            'duration': 267,
            'artist': 'Tiësto, VASSY, KSHMR',
            'genre': 'Electro House',
            'release_year': '2015',
            'thumbnail': 're:^https?://.*\.jpg',
            'view_count': int,
            'like_count': int
        }
    }, {
        'url': 'https://www.beatport.com/flamingorecordingsbps/tracks/qpwhxukynk7r/burnin-up-original-mix',
        'md5': '67bb3421c43f92b5a625c2065255925f',
        'info_dict': {
            'id': 'qpwhxukynk7r',
            'display_id': 'burnin-up-original-mix',
            'uploader': 'Flamingo Recordings',
            'uploader_id': 'flamingorecordingsbps',
            'uploader_url': 'http://www.flamingorecordings.com',
            'ext': 'mp4',
            'title': "Burnin' Up",
            'duration': 272,
            'artist': 'Flatdisk',
            'genre': 'Progressive House',
            'release_year': '2015',
            'thumbnail': 're:^https?://.*\.jpg',
            'view_count': int,
            'like_count': int
        }
    }
    ]

    def _real_extract(self, url):
        url_data = self._VALID_URL_RE.match(url)
        track_id = url_data.group('id')
        api_base = 'https://apix.beatport.com'
        api_data = self._download_json('%s/sounds/%s?format=json' % (api_base, track_id),
                                       track_id)
        if api_data['is_streamable']:
            url = self._download_json('%s/sounds/%s/stream?format=json' % (api_base, track_id),
                                      track_id, note='Downloading JSON streamdata')['url']
        else:
            raise ExtractorError('Not streamable', video_id=track_id, expected=True)
        return {
            'url': url,
            'id': track_id,
            'display_id': url_data.group('display_id'),
            'uploader': api_data.get('owner_profile', {}).get('display_name'),
            'uploader_url': api_data.get('owner_profile', {}).get('website_url'),
            'uploader_id': url_data.group('uploader_id'),
            'title': api_data['name'],
            'duration': int_or_none(api_data.get('duration'), scale=1000),
            'view_count': int_or_none(api_data.get('play_count')),
            'like_count': int_or_none(api_data.get('heart_count')),
            'artist': ', '.join(a['display_name'] for a in api_data.get('artists', [])),
            'genre': ', '.join(g['name'] for g in api_data.get('genres', [])),
            'release_year': api_data.get('pro_released_date', '').split('-')[0],
            'thumbnail': api_data.get('image')
        }
