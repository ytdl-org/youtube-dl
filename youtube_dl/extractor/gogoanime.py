# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor


class GoGoAnimeIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?gogoanime\.tv/(?P<id>[^/]+)'
    _TEST = {
        'url': 'http://gogoanime.tv/kino-no-tabi-the-beautiful-world-episode-6',
        'md5': 'd5da1bc82a1bf61990b93b7ed386683b',
        'info_dict': {
            'id': 'kino-no-tabi-the-beautiful-world-episode-6',
            'ext': 'mp4',
            'title': 'Kino no Tabi: The Beautiful World Episode 6 English Subbed',
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        title = self._html_search_regex(r'<h1>(.+?) at gogoanime</h1>', webpage, 'title')
        mobj = re.search(r'<option value="(?P<url>.+?)">(?P<fmt>.+?)<', webpage)
        (url, fmt) = (mobj.group('url'), mobj.group('fmt'))

        mobj = re.search(r'(?P<height>[0-9]+)p', fmt)
        height = int(mobj.group('height'))
        formats = [{
            'url': url,
            'format_id': fmt,
            'height': height,
            'ext': 'mp4',
        }]

        return {
            'id': video_id,
            'display_id': video_id,
            'title': title,
            'formats': formats,
        }

