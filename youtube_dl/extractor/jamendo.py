# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..compat import compat_urlparse


class JamendoIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?jamendo\.com/track/(?P<id>[0-9]+)/(?P<display_id>[\w-]+)'
    _TEST = {
        'url': 'https://www.jamendo.com/track/196219/stories-from-emona-i',
        'md5': '697564d8b10c60af35edda4fafb3fbfd',
        'info_dict': {
            'id': '196219',
            'display_id': 'stories-from-emona-i',
            'ext': 'mp3',
            'title': 'Stories from Emona I',
            'thumbnail': 're:^https?://.*\.jpg',
            'url': 'https://mp3d.jamendo.com/download/track/196219/mp32'
        }
    }

    def _real_extract(self, url):
        url_data = self._VALID_URL_RE.match(url)
        track_id = url_data.group('id')
        webpage = self._download_webpage(url, track_id)

        thumbnail = self._html_search_regex(r'<meta itemprop="image" content="(.+)">', webpage, 'thumbnail', fatal=False)
        title = self._html_search_regex('<meta itemprop="name" content="(.+)">', webpage, 'title')

        return {
            'id': track_id,
            'display_id': url_data.group('display_id'),
            'ext': 'mp3',
            'title': title,
            'thumbnail': thumbnail,
            'url': 'https://mp3d.jamendo.com/download/track/%s/mp32' % track_id
        }


class JamendoAlbumIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?jamendo\.com/album/(?P<id>[0-9]+)/(?P<display_id>[\w-]+)'
    _TEST = {
        'url': 'https://www.jamendo.com/album/121486/duck-on-cover',
        'info_dict': {
            'id': '121486',
            'title': 'Duck On Cover'
        },
        'playlist_mincount': 2,
        'playlist': [
            {
                'url': 'https://mp3d.jamendo.com/download/track/1032333/mp32',
                'md5': '84a1dfcc15c78943d9f736c0fc60191b',
                'info_dict': {
                    'id': '1032333',
                    'ext': 'mp3',
                    'title': 'Warmachine'
                }
            },
            {
                'url': 'https://mp3d.jamendo.com/download/track/1032330/mp32',
                'md5': '6a3f03c8bc01bc2f6eedef277ecaf310',
                'info_dict': {
                    'id': '1032330',
                    'ext': 'mp3',
                    'title': 'Without Your Ghost'
                }
            }
        ],
        'params': {
            'playlistend': 2
        }
    }

    def _real_extract(self, url):
        url_data = self._VALID_URL_RE.match(url)
        album_id = url_data.group('id')
        webpage = self._download_webpage(url, album_id)

        title = self._html_search_regex('<meta itemprop="name" content="(.+)">', webpage, 'title')

        track_paths = re.findall(r'<a href="(.+)" class="link-wrap js-trackrow-albumpage-link" itemprop="url">', webpage)
        entries = [
            self.url_result(compat_urlparse.urljoin(url, path), ie=JamendoIE.ie_key())
            for path in track_paths
        ]
        return {
            '_type': 'playlist',
            'id': album_id,
            'title': title,
            'entries': entries
        }
