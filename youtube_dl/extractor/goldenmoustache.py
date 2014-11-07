from __future__ import unicode_literals

import re
from .common import InfoExtractor
from ..utils import (
    parse_duration,
    int_or_none,
)


class GoldenMoustacheIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?goldenmoustache\.com/(?P<display_id>[\w-]+)-(?P<id>\d+)'
    _TEST = {
        'url': 'http://www.goldenmoustache.com/suricate-le-poker-3700/',
        'md5': '0f904432fa07da5054d6c8beb5efb51a',
        'info_dict': {
            'id': '3700',
            'ext': 'mp4',
            'title': 'Suricate - Le Poker',
            'description': 'md5:3d1f242f44f8c8cb0a106f1fd08e5dc9',
            'thumbnail': 'md5:fd41386bc1f932552622da4a7e9a7242',
        }
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')

        webpage = self._download_webpage(url, video_id)

        video_url = self._html_search_regex(r'data-src-type="mp4" data-src="([^"]+)"', webpage, 'video URL')

        title = self._html_search_regex(r'<title>(.*?) - Golden Moustache</title>', webpage, 'title')

        thumbnail = self._html_search_meta('og:image', webpage, 'thumbnail')
         
        description = self._html_search_meta('og:description', webpage, 'description')

        view_count = int_or_none(self._html_search_regex(
            r'<strong>(\d+)</strong>\s*VUES</span>', webpage, 'view count', fatal=False))

        return {
            'id': video_id,
            'url': video_url,
            'ext': 'mp4',
            'title': title,
            'description': description,
            'thumbnail': thumbnail,
            'view_count': view_count,
        }
