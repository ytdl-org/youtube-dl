from __future__ import unicode_literals

import re

from .common import InfoExtractor

class EroProfileIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?eroprofile\.com/m/videos/view/(?P<display_id>[^/]+)'
    _TEST = {
        'url': 'http://www.eroprofile.com/m/videos/view/sexy-babe-softcore',
        'md5': 'c26f351332edf23e1ea28ce9ec9de32f',
        'info_dict': {
            'id': '3733775',
            'ext': 'm4v',
            'title': 'HD MOVIES - sexy babe softcore',
            'description': 'md5:831ee50526c333eb4f6c1e58d382c295',
            'categories': list,  # NSFW
            'thumbnail': 're:https?://.*\.jpg',
            'age_limit': 18,
        }
    }

    def _real_extract(self, url):
        webpage = self._download_webpage(url, 'main')

        video_id = self._html_search_regex(r'glbUpdViews\s*\(\'\d*\',\'(\d+)\'', webpage, 'id')

        video_url = self._html_search_regex(r'<source src="([^"]+)', webpage, 'video_url')

        title = self._html_search_regex(
            r'<title>([^<]+)\s*-\s*EroProfile</title>', webpage, 'title')

        description = self._html_search_meta('description', webpage, 'description', fatal=False)

        thumbnail = self._html_search_regex(
          r'onclick="showVideoPlayer\(\)"><img src="([^"]+)', webpage, 'thumbnail', fatal=False)

        categories_str = self._html_search_meta(
            'keywords', webpage, 'categories', fatal=False)
        categories = (
            None if categories_str is None
            else categories_str.split(','))

        return {
            'id': video_id,
            'url': video_url,
            'title': title,
            'ext': 'm4v',
            'description': description,
            'thumbnail': thumbnail,
            'categories': categories,
            'age_limit': 18,
        }
