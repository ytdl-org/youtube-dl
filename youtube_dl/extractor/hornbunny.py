# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import int_or_none

class HornBunnyIE(InfoExtractor):
    _VALID_URL = r'http?://(?:www\.)?hornbunny\.com/videos/(?P<title_dash>[a-z-]+)-(?P<id>\d+)\.html'
    _TEST = {
        'url': 'http://hornbunny.com/videos/panty-slut-jerk-off-instruction-5227.html',
        'md5': '95e40865aedd08eff60272b704852ad7',
        'info_dict': {
            'id': '5227',
            'ext': 'flv',
            'title': 'panty slut jerk off instruction',
            'duration': 550
        }
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')

        webpage = self._download_webpage(url, video_id)
        title = self._html_search_regex(r'class="title">(.*?)</h2>', webpage, 'title')
        redirect_url = self._html_search_regex(r'pg&settings=(.*?)\|0"\);', webpage, 'title')
        webpage2 = self._download_webpage(redirect_url, video_id)
        video_url = self._html_search_regex(r'flvMask:(.*?);', webpage2, 'video_url')
        
        mobj = re.search(r'<strong>Runtime:</strong> (?P<minutes>\d+):(?P<seconds>\d+)</div>', webpage)
        duration = int(mobj.group('minutes')) * 60 + int(mobj.group('seconds')) if mobj else None

        view_count = self._html_search_regex(r'<strong>Views:</strong>  (\d+)</div>', webpage, 'view count', fatal=False)

        return {
            'id': video_id,
            'url': video_url,
            'title': title,
            'ext': 'flv',
            'duration': duration,
            'view_count': int_or_none(view_count),
        }
