# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor


class BigMarkerIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?bigmarker\.com/recordings/(?P<id>[a-z0-9]+)'
    _TEST = {
        'url': 'https://www.bigmarker.com/recordings/478333acea6e',
        'md5': '8efb9380119651972481f6974e0c8c06',
        'info_dict': {
            'id': '478333acea6e',
            'ext': 'mp4',
            'title': '478333acea6e',
            'url': 'https://d5ln38p3754yc.cloudfront.net/F508IZuncdvJ37XKHei8/32165f6e-4fae-4262-9f16-aa7f53142305.mp4?1602110695315',
            'author': 'Pulumi',
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        return {
            'id': video_id,
            'title': video_id,
            'author': self._search_regex(r'qaClubName:\s*(["\'])(?P<clubName>.+)\1', webpage, 'author', group='clubName', default=None),
            'url': self._search_regex(r'mp4Url:\s*(["\'])(?P<url>http.+)\1', webpage, 'url', group='url'),
        }
