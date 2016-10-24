# coding: utf-8
from __future__ import unicode_literals

import re

from ..compat import compat_urlparse
from .common import InfoExtractor


class JamendoIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?jamendo\.com/track/(?P<id>[0-9]+)/(?P<display_id>[^/?#&]+)'
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
        mobj = self._VALID_URL_RE.match(url)
        track_id = mobj.group('id')
        display_id = mobj.group('display_id')

        webpage = self._download_webpage(url, display_id)

        title = self._html_search_meta('name', webpage, 'title')

        formats = [{
            'url': 'https://%s.jamendo.com/?trackid=%s&format=%s&from=app-97dab294'
                   % (sub_domain, track_id, format_id),
            'format_id': format_id,
            'ext': ext,
            'quality': quality,
        } for quality, (format_id, sub_domain, ext) in enumerate((
            ('mp31', 'mp3l', 'mp3'),
            ('mp32', 'mp3d', 'mp3'),
            ('ogg1', 'ogg', 'ogg'),
            ('flac', 'flac', 'flac'),
        ))]
        self._sort_formats(formats)

        thumbnail = self._html_search_meta(
            'image', webpage, 'thumbnail', fatal=False)

        return {
            'id': track_id,
            'display_id': display_id,
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
        'playlist': [{
            'md5': 'e1a2fcb42bda30dfac990212924149a8',
            'info_dict': {
                'id': '1032333',
                'ext': 'flac',
                'title': 'Warmachine'
            }
        }, {
            'md5': '1f358d7b2f98edfe90fd55dac0799d50',
            'info_dict': {
                'id': '1032330',
                'ext': 'flac',
                'title': 'Without Your Ghost'
            }
        }],
        'params': {
            'playlistend': 2
        }
    }

    def _real_extract(self, url):
        mobj = self._VALID_URL_RE.match(url)
        album_id = mobj.group('id')

        webpage = self._download_webpage(url, mobj.group('display_id'))

        title = self._html_search_meta('name', webpage, 'title')

        entries = [
            self.url_result(
                compat_urlparse.urljoin(url, m.group('path')),
                ie=JamendoIE.ie_key(),
                video_id=self._search_regex(
                    r'/track/(\d+)', m.group('path'),
                    'track id', default=None))
            for m in re.finditer(
                r'<a[^>]+href=(["\'])(?P<path>(?:(?!\1).)+)\1[^>]+class=["\'][^>]*js-trackrow-albumpage-link',
                webpage)
        ]

        return self.playlist_result(entries, album_id, title)
