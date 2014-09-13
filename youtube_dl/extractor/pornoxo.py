from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    str_to_int,
)


class PornoXOIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?pornoxo\.com/videos/(?P<id>\d+)/(?P<display_id>[^/]+)\.html'
    _TEST = {
        'url': 'http://www.pornoxo.com/videos/7564/striptease-from-sexy-secretary.html',
        'md5': '582f28ecbaa9e6e24cb90f50f524ce87',
        'info_dict': {
            'id': '7564',
            'ext': 'flv',
            'title': 'Striptease From Sexy Secretary!',
            'description': 'Striptease From Sexy Secretary!',
            'categories': list,  # NSFW
            'thumbnail': 're:https?://.*\.jpg$',
            'age_limit': 18,
        }
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')

        webpage = self._download_webpage(url, video_id)

        video_url = self._html_search_regex(
            r'\'file\'\s*:\s*"([^"]+)"', webpage, 'video_url')

        title = self._html_search_regex(
            r'<title>([^<]+)\s*-\s*PornoXO', webpage, 'title')

        description = self._html_search_regex(
            r'<meta name="description" content="([^"]+)\s*featuring',
            webpage, 'description', fatal=False)

        thumbnail = self._html_search_regex(
            r'\'image\'\s*:\s*"([^"]+)"', webpage, 'thumbnail', fatal=False)

        view_count = str_to_int(self._html_search_regex(
            r'[vV]iews:\s*([0-9,]+)', webpage, 'view count', fatal=False))

        categories_str = self._html_search_regex(
            r'<meta name="description" content=".*featuring\s*([^"]+)"',
            webpage, 'categories', fatal=False)
        categories = (
            None if categories_str is None
            else categories_str.split(','))

        return {
            'id': video_id,
            'url': video_url,
            'title': title,
            'description': description,
            'thumbnail': thumbnail,
            'categories': categories,
            'view_count': view_count,
            'age_limit': 18,
        }
