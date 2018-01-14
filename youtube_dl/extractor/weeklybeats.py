# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor


class WeeklyBeatsIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?weeklybeats\.com/(.+)/music/(?P<id>.+)'
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
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        return {
            'id': video_id,
            'title': self._search_regex(r'<div[^>]+id=(["\'])item_title\1>[^>]*<h3>(?P<title>[^<]+)', webpage, 'title', group='title'),
            'description': self._og_search_description(webpage),
            'uploader': self._search_regex(r'<a[^>]+class=(["\'])[^"\']+artist\1[^>]*>View by:(?P<uploader>[^<]+)', webpage, 'uploader', group='uploader'),
            'url': self._search_regex(r'<a[^>]+id=(["\'])item_download\1[^>]+href=\1(?P<url>[^"\']+)\?', webpage, 'url', group="url"),
            # TODO more properties (see youtube_dl/extractor/common.py)
        }
