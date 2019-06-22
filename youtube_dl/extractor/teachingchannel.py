# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor


class TeachingChannelIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?teachingchannel\.org/video/(?P<id>[^/?#]+)'
    _TEST = {
        'url': 'https://www.teachingchannel.org/video/teacher-teaming-evolution',
        'md5': 'ce11b12f58d87e02e6d3c1f5fd788c07',
        'info_dict': {
            'id': '3swwlzkT',
            'ext': 'mp4',
            'title': 'A History of Teaming',
            'description': 'md5:2a9033db8da81f2edffa4c99888140b3',
            'upload_date': '20170316',
            'timestamp': 1489691297,
            'duration': 422.0,
        }
    }

    def _real_extract(self, url):
        display_id = self._match_id(url)
        webpage = self._download_webpage(url, display_id)
        video_id = self._search_regex(
            (r'data-mid=(["\'])(?P<id>(?:(?!\1).)+)\1',
             r'id=(["\'])jw-video-player-(?P<id>(?:(?!\1).)+)\1'),
            webpage, 'video_id', group='id')
        return self.url_result('jwplatform:' + video_id, 'JWPlatform', video_id)
