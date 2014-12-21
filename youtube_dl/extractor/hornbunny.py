# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    int_or_none,
    parse_duration,
)


class HornBunnyIE(InfoExtractor):
    _VALID_URL = r'http?://(?:www\.)?hornbunny\.com/videos/(?P<title_dash>[a-z-]+)-(?P<id>\d+)\.html'
    _TEST = {
        'url': 'http://hornbunny.com/videos/panty-slut-jerk-off-instruction-5227.html',
        'md5': '95e40865aedd08eff60272b704852ad7',
        'info_dict': {
            'id': '5227',
            'ext': 'flv',
            'title': 'panty slut jerk off instruction',
            'duration': 550,
            'age_limit': 18,
        }
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')

        webpage = self._download_webpage(
            url, video_id, note='Downloading initial webpage')
        title = self._html_search_regex(
            r'class="title">(.*?)</h2>', webpage, 'title')
        redirect_url = self._html_search_regex(
            r'pg&settings=(.*?)\|0"\);', webpage, 'title')
        webpage2 = self._download_webpage(redirect_url, video_id)
        video_url = self._html_search_regex(
            r'flvMask:(.*?);', webpage2, 'video_url')

        duration = parse_duration(self._search_regex(
            r'<strong>Runtime:</strong>\s*([0-9:]+)</div>',
            webpage, 'duration', fatal=False))
        view_count = int_or_none(self._search_regex(
            r'<strong>Views:</strong>\s*(\d+)</div>',
            webpage, 'view count', fatal=False))

        return {
            'id': video_id,
            'url': video_url,
            'title': title,
            'ext': 'flv',
            'duration': duration,
            'view_count': view_count,
            'age_limit': 18,
        }
