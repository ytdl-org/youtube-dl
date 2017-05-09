from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import determine_ext

class GotPornIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?xvideos\.com/video(?P<id>[0-9]+)(?:.*)'
    _VALID_URL = r'http://www\.gotporn\.com/(?P<display_id>[^/]+)/video-(?P<id>[0-9]+)'
    _TEST = {
        'url': 'http://www.gotporn.com/big-boobs-babe/video-5661549',
        'md5': '9ad371d58a8ee709d8321a548d6e5d2d',
        'info_dict': {
            'id': '5661549',
            'ext': 'mp4',
            'title': 'Big Boobs Babe',
            'age_limit': 18,
        }
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')
        display_id = mobj.group('display_id')
        if not display_id:
            display_id = video_id

        webpage = self._download_webpage(url, video_id)

        title = self._html_search_regex(r'<h1\s+class=[\'"]title-block[\'"]>\s*([^<]+)', webpage, 'title')
        thumbnail_url = self._html_search_regex(r'<link\s+itemprop=[\'"]thumbnailUrl[\'"]\s+href=[\'"]([^\'"]+)', webpage, 'thumbnail_url')
        video_url = self._html_search_regex(r'<source.+?src=[\'"]([^\'"]+)[\'"]', webpage, 'video_url')

        return {
            'id': video_id,
            'display_id': display_id,
            'url': video_url,
            'thumbnail': thumbnail_url,
            'ext': determine_ext(video_url, 'mp4'),
            'title': title,
            'age_limit': 18,
        }
