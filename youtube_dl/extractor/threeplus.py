# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from .threeqsdn import ThreeQSDNIE
from ..utils import (
    get_element_by_class,
    smuggle_url,
)


class ThreePlusIE(InfoExtractor):
    IE_NAME = '3 Plus'
    _VALID_URL = r'https?://(?:www\.)3plus\.(?:tv|ch)/(?!videos)(?P<id>.+)'

    _TESTS = [{
        # Real video ID known in advance
        'url': 'http://www.3plus.tv/episode/mama-ich-bin-schwanger/teenager-werden-muetter-folge-3',
        'md5': '424d9bd2b10e7d4149299bef74e5ddd2',
        'info_dict': {
            'id': 'de1b7745-11d6-11e6-b427-0cc47a188158',
            'ext': 'mp4',
            'title': 'MAMA ICH BIN SCHWANGER ST01 - Episode 03',
            'description': 'md5:2b93142fd82f4b5460f97b13fee40eb8',
        },
        'expected_warnings': ['Unable to download f4m manifest', 'Failed to parse JSON'],
    }, {
        # Real video ID not known in advance
        'url': 'http://www.3plus.tv/episode/bumann-der-restauranttester/la-sosta',
        'info_dict': {
            'id': '7b0cc34b-f527-11e6-a78b-0cc47a188158',
            'ext': 'mp4',
            'title': 'BRT09 Ep02 - La Sosta (TG)',
            'description': 'md5:663ea575f4a3be7069f84bf4933ed40a',
        },
        'params': {
            'skip_download': True,
        },
        'expected_warnings': ['Unable to download f4m manifest', 'Failed to parse JSON'],
    }]

    def _real_extract(self, url):
        display_id = self._match_id(url)
        webpage = self._download_webpage(url, display_id)
        video_id = self._search_regex(
            r'var\s+sdnPlayoutId\s*=\s*"([0-9a-f\-]{36})"', webpage, 'video id')
            
        return self.url_result(
            smuggle_url('3qsdn:%s' % video_id, {'first_video_only': True}),
            ThreeQSDNIE.ie_key())


class ThreePlusPlaylistIE(InfoExtractor):
    IE_NAME = '3 Plus Playlists'
    _VALID_URL = r'https?://(?:www\.)3plus\.(?:tv|ch)/videos/(?P<id>.+)'

    _TEST = {
        'url': 'http://www.3plus.tv/videos/6726',
        'info_dict': {
            'id': '6726',
            'title': 'Camping Paradiso Grandioso',
        },
        'playlist_count': 4,
    }

    def _real_extract(self, url):
        playlist_id = self._match_id(url)
        webpage = self._download_webpage(url, playlist_id)

        title = get_element_by_class('pane-title', webpage)
        entries = [self.url_result(
            smuggle_url('3qsdn:%s' % m.group('id'), {'first_video_only': True})) for m in re.finditer(
            r'<div[^>]+class\s*=\s*"field-content\s*"\s*>(?P<id>[0-9a-f\-]{36})</div>', webpage)]

        return self.playlist_result(entries, playlist_id, title)
