# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import (
    int_or_none,
)

import re


class CaffeineIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?caffeine\.tv/.+/video/(?P<video_id>[0-9a-f-]+)'
    _TEST = {
        'url': 'https://www.caffeine.tv/TsuSurf/video/cffc0a00-e73f-11ec-8080-80017d29f26e',
        'info_dict': {
            'id': 'cffc0a00-e73f-11ec-8080-80017d29f26e',
            'ext': 'mp4',
            'title': 'GOOOOD MORNINNNNN #highlights',
            'uploader': 'TsuSurf',
            'duration': 3145,
        }
    }

    def _real_extract(self, url):
        video_id = re.match(self._VALID_URL, url).group('video_id')
        json_data = self._download_json('https://api.caffeine.tv/social/public/activity/' + video_id, video_id)
        broadcast_info = json_data['broadcast_info']
        title = broadcast_info['broadcast_title']
        video_url = broadcast_info['video_url']

        formats = self._extract_m3u8_formats(
            video_url, video_id, 'mp4')
        self._sort_formats(formats)

        return {
            'id': video_id,
            'title': title,
            'uploader': json_data['username'],
            'duration': int_or_none(broadcast_info['content_duration']),
            'like_count': int_or_none(json_data['like_count']),
            'formats': formats,
        }
