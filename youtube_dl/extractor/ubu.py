from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import int_or_none


class UbuIE(InfoExtractor):
    _VALID_URL = r'http://(?:www\.)?ubu\.com/film/(?P<id>[\da-z_-]+)\.html'
    _TEST = {
        'url': 'http://ubu.com/film/her_noise.html',
        'md5': '8edd46ee8aa6b265fb5ed6cf05c36bc9',
        'info_dict': {
            'id': 'her_noise',
            'ext': 'mp4',
            'title': 'Her Noise - The Making Of (2007)',
            'duration': 3600,
        },
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')

        webpage = self._download_webpage(url, video_id)

        title = self._html_search_regex(
            r'<title>.+?Film &amp; Video: ([^<]+)</title>', webpage, 'title')

        duration = int_or_none(self._html_search_regex(
            r'Duration: (\d+) minutes', webpage, 'duration', fatal=False, default=None))
        if duration:
            duration *= 60

        formats = []

        FORMAT_REGEXES = [
            ['sq', r"'flashvars'\s*,\s*'file=([^']+)'"],
            ['hq', r'href="(http://ubumexico\.centro\.org\.mx/video/[^"]+)"']
        ]

        for format_id, format_regex in FORMAT_REGEXES:
            m = re.search(format_regex, webpage)
            if m:
                formats.append({
                    'url': m.group(1),
                    'format_id': format_id,
                })

        return {
            'id': video_id,
            'title': title,
            'duration': duration,
            'formats': formats,
        }
