from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    parse_duration,
    int_or_none,
    qualities,
    determine_ext,
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
            'thumbnail': 're:^https?://.*\.jpg$',
            'duration': 302,
            'age_limit': 18,
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)

        webpage = self._download_webpage(url, video_id)

        title = self._html_search_regex(
            r'<title>([^<]+)</title>', webpage, 'title')
        description = self._html_search_meta(
            'description', webpage, 'description')
        thumbnail = self._html_search_regex(
            r'poster="([^"]+)"', webpage, 'thumbnail', fatal=False)

        duration = parse_duration(self._search_regex(
            r'itemprop="duration">\s*(\d+:\d+)\s*<',
            webpage, 'duration', fatal=False))

        view_count = int_or_none(self._html_search_regex(
            r'class="views">(?:<noscript>)?\s*(\d+)\s*<',
            webpage, 'view count', fatal=False))
        comment_count = int_or_none(self._html_search_regex(
            r'(\d+)</b> Comments?',
            webpage, 'comment count', fatal=False))

        formats = []
        quality = qualities(['mp4', 'flv'])
        for video_url in re.findall(r'<(?:source|video) src="([^"]+)"', webpage):
            video_ext = determine_ext(video_url)
            formats.append({
                'url': video_url,
                'format_id': video_ext,
                'quality': quality(video_ext),
            })
        self._sort_formats(formats)

        return {
            'id': video_id,
            'title': title,
            'description': description,
            'thumbnail': thumbnail,
            'duration': duration,
            'view_count': view_count,
            'comment_count': comment_count,
            'formats': formats,
            'age_limit': 18,
        }
