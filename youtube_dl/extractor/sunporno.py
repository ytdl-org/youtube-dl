from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    parse_duration,
    int_or_none,
)


class SunPornoIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?sunporno\.com/videos/(?P<id>\d+)'
    _TEST = {
        'url': 'http://www.sunporno.com/videos/807778/',
        'md5': '6457d3c165fd6de062b99ef6c2ff4c86',
        'info_dict': {
            'id': '807778',
            'ext': 'flv',
            'title': 'md5:0a400058e8105d39e35c35e7c5184164',
            'description': 'md5:a31241990e1bd3a64e72ae99afb325fb',
            'duration': 302,
        }
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')

        webpage = self._download_webpage(url, video_id)

        video_url = self._html_search_regex(
            r'videoSource\s*=\s*\'<source\s*src="([^"]*)"', webpage, 'video URL')

        title = self._html_search_regex(r'<title>([^<]*)</title>', webpage, 'title')

        description = self._html_search_regex(
            r'<meta name="description" content="([^"]*)"', webpage, 'description', fatal=False)
        
        thumbnail = self._html_search_regex(
            r'poster="([^"]*)"', webpage, 'thumbnail', fatal=False)

        duration = parse_duration(self._search_regex(
            r'<span>Duration: (\d+:\d+)</span>', webpage, 'duration', fatal=False))

        view_count = int_or_none(self._html_search_regex(
            r'<span class="views">(\d+)</span>', webpage, 'view count', fatal=False))

        return {
            'id': video_id,
            'url': video_url,
            'title': title,
            'description': description,
            'thumbnail': thumbnail,
            'duration': duration,
            'view_count': view_count,
        }
