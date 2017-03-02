# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from .threeqsdn import ThreeQSDNIE
from ..utils import get_element_by_class


class ThreePlusBaseIE(InfoExtractor):
    _HOST_URL = 'http://playout.3qsdn.com/'

    def _get_title_and_description(self, video_id):
        webpage = self._download_webpage(
            self._HOST_URL + video_id, video_id)
        title = self._og_search_title(webpage)
        description = self._og_search_description(webpage)
        return title, description

    def _get_real_video_id(self, video_id):
        video_info = self._download_webpage(self._HOST_URL + video_id + '?js=true', video_id)
        video_id = self._search_regex(
            r'sdnPlayoutId\s*:\s*\'(.+?)\'', video_info, 'Real video id', default=video_id)
        video_id = video_id.replace('\\x2D', '-')
        return video_id

    def _extract_from_id(self, video_id):
        video_id = self._get_real_video_id(video_id)
        title, description = self._get_title_and_description(video_id)
        return {
            '_type': 'url_transparent',
            'ie_key': ThreeQSDNIE.ie_key(),
            'url': self._HOST_URL + video_id,
            'id': video_id,
            'title': title,
            'description': description,
        }


class ThreePlusIE(ThreePlusBaseIE):
    IE_NAME = '3 Plus'
    _VALID_URL = r'https?://(?:www\.)3plus\.(?:tv|ch)/(?!videos)(?P<id>.+)'

    _TESTS = [{
        # Real video ID known in advance
        'url': 'http://www.3plus.tv/episode/mama-ich-bin-schwanger/teenager-werden-muetter-folge-3',
        'info_dict': {
            'id': 'de1b7745-11d6-11e6-b427-0cc47a188158',
            'ext': 'mp4',
            'title': 'MAMA ICH BIN SCHWANGER ST01 - Episode 03',
            'description': 'md5:2b93142fd82f4b5460f97b13fee40eb8',
        },
        'params': {
            'skip_download': True,
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

        return self._extract_from_id(video_id)


class ThreePlusPlaylistIE(ThreePlusBaseIE):
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
        entries = [self._extract_from_id(m.group('id')) for m in re.finditer(
            r'<div[^>]+class\s*=\s*"field-content\s*"\s*>(?P<id>[0-9a-f\-]{36})</div>', webpage)]
        return self.playlist_result(entries, playlist_id, title)
