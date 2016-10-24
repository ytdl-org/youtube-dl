# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..compat import compat_urlparse


class JamendoIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?jamendo\.com/track/(?P<id>[0-9]+)/(?P<display_id>[\w-]+)'
    _TEST = {
        'url': 'https://www.jamendo.com/track/196219/stories-from-emona-i',
        'md5': '6e9e82ed6db98678f171c25a8ed09ffd',
        'info_dict': {
            'id': '196219',
            'display_id': 'stories-from-emona-i',
            'ext': 'flac',
            'title': 'Stories from Emona I',
            'thumbnail': 're:^https?://.*\.jpg'
        }
    }

    def _real_extract(self, url):
        url_data = self._VALID_URL_RE.match(url)
        track_id = url_data.group('id')
        webpage = self._download_webpage(url, track_id)

        thumbnail = self._html_search_meta(
            'image', webpage, 'thumbnail', fatal=False)
        title = self._html_search_meta('name', webpage, 'title')
        formats = [
            {
                'format_id': 'mp31',
                'url': 'https://mp3l.jamendo.com/?trackid=%s&format=mp31'
                % track_id,
                'ext': 'mp3'
            },
            {
                'format_id': 'mp32',
                'url': 'https://mp3d.jamendo.com/?trackid=%s&format=mp32'
                % track_id,
                'ext': 'mp3'
            },
            {
                'format_id': 'ogg',
                'url': 'https://ogg.jamendo.com/?trackid=%s&format=ogg1'
                % track_id,
                'ext': 'ogg'
            },
            {
                'format_id': 'flac',
                'url': 'https://flac.jamendo.com/?trackid=%s&format=flac'
                % track_id,
                'ext': 'flac'
            }
        ]
        self._check_formats(formats, video_id=track_id)
        return {
            'id': track_id,
            'display_id': url_data.group('display_id'),
            'thumbnail': thumbnail,
            'title': title,
            'formats': formats
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
                'md5': 'e1a2fcb42bda30dfac990212924149a8',
                'info_dict': {
                    'id': '1032333',
                    'ext': 'flac',
                    'title': 'Warmachine'
                }
            },
            {
                'md5': '1f358d7b2f98edfe90fd55dac0799d50',
                'info_dict': {
                    'id': '1032330',
                    'ext': 'flac',
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

        title = self._html_search_meta('name', webpage, 'title')

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
