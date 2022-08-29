# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor


class BandlabIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?bandlab\.com/post/(?P<id>[^/]+)'

    _TEST = {
        'url': 'https://www.bandlab.com/post/f5f04998635a44ea819cacdba7ae2076_f8d8574c3bdaec11b6562818783151a1',
        'info_dict': {
            'id': 'f5f04998635a44ea819cacdba7ae2076_f8d8574c3bdaec11b6562818783151a1',
            'ext': 'm4a',
            'title': 'ON MY OWN (unreleased)',
            'artist': 'Michael MacDonald',
        },
    }

    def _real_extract(self, url):
        track_id = self._match_id(url)
        config = self._download_json(
            'http://www.bandlab.com/api/v1.3/posts/%s' % track_id, track_id)
        track_url = config['track']['sample']['audioUrl']

        return {
            'id': track_id,
            'title': config['track']['name'],
            'url': track_url,
            'artist': config['creator']['name']
        }


class BandlabAlbumIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?bandlab\.com/[^/]+/albums/(?P<id>[^/]+)'
    _TEST = {
        'url': 'https://www.bandlab.com/sbsdasani/albums/dc26e307-e51f-ed11-95d7-002248452390',
        'playlist': [
            {
                'info_dict': {
                    'id': '91feeb36-8e10-4c91-ae57-ffac0a98c6b4',
                    'title': 'How\'d I Lose You? (Intro)',
                    'ext': 'm4a',
                },
            },
            {
                'info_dict': {
                    'id': 'd87c50a2-70cb-4937-9b97-3ae8646ca3aa',
                    'title': 'Money $$$',
                    'ext': 'm4a',
                },
            },
            {
                'info_dict': {
                    'id': 'ff2909ff-348f-448d-9d2c-7edbf2f0ec5e',
                    'title': 'You\'ll Be Mine',
                    'ext': 'm4a',
                },
            },
            {
                'info_dict': {
                    'id': '53786c38-1f3c-4921-9271-793a64af7186',
                    'title': 'Who You Are',
                    'ext': 'm4a',
                },
            },
            {
                'info_dict': {
                    'id': '0394bb27-113f-4d19-b902-f9c1fe6ba8a8',
                    'title': 'In Your Eyes',
                    'ext': 'm4a',
                },
            },
            {
                'info_dict': {
                    'id': '2aa44689-c7fa-4d0e-b28a-e0d1dd570372',
                    'title': 'The Same',
                    'ext': 'm4a',
                },
            },
            {
                'info_dict': {
                    'id': '281fe589-a559-4260-802d-78a6c7a973d8',
                    'title': 'Fall In Love',
                    'ext': 'm4a',
                },
            },
            {
                'info_dict': {
                    'id': '83a9dc0a-702f-40fd-82f6-ab847f6a7b46',
                    'title': 'Tried So Hard',
                    'ext': 'm4a',
                },
            },
            {
                'info_dict': {
                    'id': '3f6a4a1c-eb73-449f-bd45-f7958d6f2de1',
                    'title': 'The End Of Everything',
                    'ext': 'm4a',
                },
            }
        ],
        'info_dict': {
            'id': 'dc26e307-e51f-ed11-95d7-002248452390',
            'album': 'ENDLESS SUMMER',
            'artist': 'Michael MacDonald'
        },
    }

    def _real_extract(self, url):
        album_id = self._match_id(url)
        config = self._download_json(
            'http://www.bandlab.com/api/v1.3/albums/%s' % album_id, album_id)
        tracks = config['posts']
        entries = []
        for track in tracks:
            if 'track' in track:
                url = track['track']['sample']['audioUrl']
                name = track['track']['name']
            elif 'revision' in track:
                url = track['revision']['mixdown']['file']
                name = track['revision']['song']['name']
            else:
                raise Exception("Neither track nor revision found in 'posts' object")
            id_regex = r'.+/(?P<id>[^/]+).m4a'
            id = re.compile(id_regex).match(url).group('id')
            entries.append({
                'url': url,
                'id': id,
                'title': name
            })

        return {
            '_type': 'playlist',
            'id': album_id,
            'album': config['name'],
            'artist': config['creator']['name'],
            'entries': entries
        }


class BandlabPlaylistIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?bandlab\.com/[^/]+/collections/(?P<id>[^/]+)'
    _TEST = {
        'url': 'https://www.bandlab.com/hexatetrahedronx/collections/8fb1041c-e865-eb11-9889-0050f28a2802',
        'playlist': [
            {
                'info_dict': {
                    'id': '8f37e4aa-92c4-eb11-a7ad-0050f280467f',
                    'title': 'psych ward',
                    'ext': 'm4a'
                }
            }
        ],
        'info_dict': {
            'id': '8fb1041c-e865-eb11-9889-0050f28a2802',
            'playlist': 'DOOMTAPE'
        }
    }

    def _real_extract(self, url):
        playlist_id = self._match_id(url)
        config = self._download_json(
            'http://www.bandlab.com/api/v1.3/collections/%s' % playlist_id, playlist_id)
        tracks = config['posts']
        entries = []
        for track in tracks:
            if 'track' in track:
                url = track['track']['sample']['audioUrl']
                name = track['track']['name']
            elif 'revision' in track:
                url = track['revision']['mixdown']['file']
                name = track['revision']['song']['name']
            else:
                raise Exception("Neither track nor revision found in 'posts' object")
            id_regex = r'.+/(?P<id>[^/]+).m4a'
            id = re.compile(id_regex).match(url).group('id')
            entries.append({
                'url': url,
                'id': id,
                'title': name
            })

        return {
            '_type': 'playlist',
            'id': playlist_id,
            'playlist': config['name'],
            'entries': entries
        }
