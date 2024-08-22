# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    int_or_none,
)


class JizzBunkerIE(InfoExtractor):
    _VALID_URL = r'https://(?:www\.)?jizzbunker\.com/(?P<id>\d+)/(?P<display_id>.+)\.html'
    _TEST = {
        'url': 'https://jizzbunker.com/22295/blonde-girl-strips-at-home.html',
        'info_dict': {
            'id': '22295',
            'display_id': 'blonde-girl-strips-at-home',
            'ext': '480',
            'title': 'Blonde girl strips at home',
            'thumbnail': r're:^https?://.*\.jpg$',
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        display_id = re.match(self._VALID_URL, url).group('display_id')

        webpage = self._download_webpage(url, video_id)

        title = self._html_search_regex(r'<h1[^>]*>\n?(.+?)</h1>', webpage, 'title')
        thumbnail = self._og_search_thumbnail(webpage, default=None)
        duration = int_or_none(self._search_regex(r'dur: (\d+)', webpage, 'duration', default=None))
        video_url = self._search_regex(r"type:'video/mp4',src:'(https://[^']+)", webpage, 'video url')

        return {
            'id': video_id,
            'display_id': display_id,
            'title': title,
            'thumbnail': thumbnail,
            'duration': duration,
            'url': video_url,
        }
