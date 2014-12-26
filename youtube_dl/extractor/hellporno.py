from __future__ import unicode_literals

import re

from .common import InfoExtractor

class HellPornoIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?hellporno\.com/videos/(?P<display_id>[^/]+)'
    _TEST = {
        'url': 'http://hellporno.com/videos/dixie-is-posing-with-naked-ass-very-erotic/',
        'md5': '1fee339c610d2049699ef2aa699439f1',
        'info_dict': {
            'id': '149116',
            'ext': 'mp4',
            'title': 'Dixie is posing with naked ass very erotic',
            'description': 'md5:5ba02cbf31eff820147b3cc25306d89a',
            'categories': list,  # NSFW
            'thumbnail': 're:https?://.*\.jpg$',
            'age_limit': 18,
        }
    }

    def _real_extract(self, url):
        webpage = self._download_webpage(url, 'main')

        video_id = self._html_search_regex(r'video_id:\s*\'([^\']+)\'', webpage, 'id')

        video_url = self._html_search_regex(r'video_url:\s*\'([^\']+)\'', webpage, 'video_url')

        ext = self._html_search_regex(r'postfix:\s*\'([^\']+)\'', webpage, 'ext')[1:]

        title = self._html_search_regex(
            r'<title>([^<]+)\s*-\s*Hell Porno</title>', webpage, 'title')

        description = self._html_search_meta('description', webpage, 'description', fatal=False)

        thumbnail = self._html_search_regex(
            r'preview_url:\s*\'([^\']+)\'',
            webpage, 'thumbnail', fatal=False)

        categories_str = self._html_search_regex(
            r'<meta name="keywords" content="([^"]+)"', webpage, 'categories', fatal=False)
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
