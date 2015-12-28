from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    int_or_none,
    qualities,
)


class UbuIE(InfoExtractor):
    _VALID_URL = r'http://(?:www\.)?ubu\.com/film/(?P<id>[\da-z_-]+)\.html'
    _TEST = {
        'url': 'http://ubu.com/film/her_noise.html',
        'md5': '138d5652618bf0f03878978db9bef1ee',
        'info_dict': {
            'id': 'her_noise',
            'ext': 'm4v',
            'title': 'Her Noise - The Making Of (2007)',
            'duration': 3600,
        },
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        title = self._html_search_regex(
            r'<title>.+?Film &amp; Video: ([^<]+)</title>', webpage, 'title')

        duration = int_or_none(self._html_search_regex(
            r'Duration: (\d+) minutes', webpage, 'duration', fatal=False),
            invscale=60)

        formats = []
        FORMAT_REGEXES = [
            ('sq', r"'flashvars'\s*,\s*'file=([^']+)'"),
            ('hq', r'href="(http://ubumexico\.centro\.org\.mx/video/[^"]+)"'),
        ]
        preference = qualities([fid for fid, _ in FORMAT_REGEXES])
        for format_id, format_regex in FORMAT_REGEXES:
            m = re.search(format_regex, webpage)
            if m:
                formats.append({
                    'url': m.group(1),
                    'format_id': format_id,
                    'preference': preference(format_id),
                })
        self._sort_formats(formats)

        return {
            'id': video_id,
            'title': title,
            'duration': duration,
            'formats': formats,
        }
