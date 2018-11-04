# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor


class HomeMoviesTubeIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?homemoviestube\.com/videos/(?P<id>[0-9]+)/(?P<display_id>[^/]+)\.html'
    _TEST = {
        'url': 'https://www.homemoviestube.com/videos/314747/creamed-again.html',
        'md5': 'a1f827520d82c0b70da391a8aed410c9',
        'info_dict': {
            'id': '314747',
            'display_id': 'creamed-again',
            'ext': 'mp4',
            'title': 'Creamed again',
        }
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        display_id = mobj.group('display_id')
        video_id = mobj.group('id')

        webpage = self._download_webpage(url, display_id)

        video_url = self._html_search_regex(
            r'<source src="(.+?)"', webpage, 'video URL')

        title = self._html_search_regex(r'<h1>(.+?)</h1>', webpage, 'title')

        return {
            'id': video_id,
            'display_id': display_id,
            'title': title,
            'url': video_url,
        }
