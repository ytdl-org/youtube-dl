from __future__ import unicode_literals

import re

from .common import InfoExtractor


class SexuIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?sexu\.com/(?P<id>\d+)'
    _TEST = {
        'url': 'http://sexu.com/961791/',
        'md5': 'ff615aca9691053c94f8f10d96cd7884',
        'info_dict': {
            'id': '961791',
            'ext': 'mp4',
            'title': 'md5:4d05a19a5fc049a63dbbaf05fb71d91b',
            'description': 'md5:c5ed8625eb386855d5a7967bd7b77a54',
            'categories': list,  # NSFW
            'thumbnail': 're:https?://.*\.jpg$',
            'age_limit': 18,
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        quality_arr = self._search_regex(
            r'sources:\s*\[([^\]]+)\]', webpage, 'forrmat string')
        formats = [{
            'url': fmt[0].replace('\\', ''),
            'format_id': fmt[1],
            'height': int(fmt[1][:3]),
        } for fmt in re.findall(r'"file":"([^"]+)","label":"([^"]+)"', quality_arr)]
        self._sort_formats(formats)

        title = self._html_search_regex(
            r'<title>([^<]+)\s*-\s*Sexu\.Com</title>', webpage, 'title')

        description = self._html_search_meta(
            'description', webpage, 'description')

        thumbnail = self._html_search_regex(
            r'image:\s*"([^"]+)"',
            webpage, 'thumbnail', fatal=False)

        categories_str = self._html_search_meta(
            'keywords', webpage, 'categories')
        categories = (
            None if categories_str is None
            else categories_str.split(','))

        return {
            'id': video_id,
            'title': title,
            'description': description,
            'thumbnail': thumbnail,
            'categories': categories,
            'formats': formats,
            'age_limit': 18,
        }
