from __future__ import unicode_literals

import re

from .common import InfoExtractor

class AlphaPornoIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?alphaporno\.com/videos/(?P<display_id>[^/]+)'
    _TEST = {
        'url': 'http://www.alphaporno.com/videos/sensual-striptease-porn-with-samantha-alexandra/',
        'md5': 'feb6d3bba8848cd54467a87ad34bd38e',
        'info_dict': {
            'id': '258807',
            'ext': 'mp4',
            'title': 'Sensual striptease porn with Samantha Alexandra - Striptease Porn',
            'description': 'md5:c4447dc80e5be4c5f2711f7806e45424',
            'categories': list,  # NSFW
            'thumbnail': 're:https?://.*\.jpg$',
            'age_limit': 18,
        }
    }

    def _real_extract(self, url):
        webpage = self._download_webpage(url, 'main')

        video_id = self._html_search_regex(r'video_id:\s*\'([^\']+)\'', webpage, 'id')

        video_url = self._html_search_regex(r'video_url:\s*\'([^\']+)\'', webpage, 'video_url')

        ext = self._html_search_meta('encodingFormat', webpage, 'ext')[1:]

        title = self._html_search_regex(
            r'<title>([^<]+)</title>', webpage, 'title')

        description = self._html_search_meta('description', webpage, 'description', fatal=False)

        thumbnail = self._html_search_meta('thumbnail', webpage, 'thumbnail', fatal=False)

        categories_str = self._html_search_meta(
            'keywords', webpage, 'categories', fatal=False)
        categories = (
            None if categories_str is None
            else categories_str.split(','))

        return {
            'id': video_id,
            'url': video_url,
            'title': title,
            'ext': ext,
            'description': description,
            'thumbnail': thumbnail,
            'categories': categories,
            'age_limit': 18,
        }
