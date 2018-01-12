# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor


class WeeklyBeatsIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?weeklybeats\.com/(.+)/music/(.+)'
    _TEST = {
        'url': 'https://weeklybeats.com/pulsn/music/week-1-bass-drop',
        'md5': '03465d0fa355147822d2ba1100a82c7c',
        'info_dict': {
            'id': 'week-1-bass-drop',
            'ext': 'mp3',
            'title': 'Week 1: Bass Drip ',
            'url': 'https://weeklybeats.s3.amazonaws.com/music/2012/pulsn_weeklybeats-2012_1_week-1-bass-drop.mp3',
            'uploader': 'pulsn',
            'description': 'A blend of IDM noises mixed with Berlin styled arps and ambient pads.'
        }
    }

    def _real_extract(self, url):
        video_id = self._search_regex(r'https://weeklybeats.com/[^/]+/music/([^/]*)/?', url, 'video_id')
        webpage = self._download_webpage(url, video_id)

        return {
            'id': video_id,
            'title': self._search_regex(r'<meta[^>]+property="og:title"[^>]+content="([^\"]+)"[^>]*>', webpage, 'title', fatal=False),
            'description': self._search_regex(r'<meta[^>]+property="og:description"[^>]+content="([^\"]*)"[^>]*>', webpage, 'description', fatal=False),
            'uploader': self._search_regex(r'<a[^>]+class="form_popular_tags ?artist"[^>]*>View by:([^<]+)<', webpage, 'uploader', fatal=False),
            'url': self._search_regex(r'mp3: \'([^\']+)\'', webpage, 'url')
            # TODO more properties (see youtube_dl/extractor/common.py)
        }
