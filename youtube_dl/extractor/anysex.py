from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    parse_duration,
    int_or_none,
)


class AnySexIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?anysex\.com/(?P<id>\d+)'
    _TEST = {
        'url': 'http://anysex.com/156592/',
        'md5': '023e9fbb7f7987f5529a394c34ad3d3d',
        'info_dict': {
            'id': '156592',
            'ext': 'mp4',
            'title': 'Busty and sexy blondie in her bikini strips for you',
            'description': 'md5:de9e418178e2931c10b62966474e1383',
            'categories': ['Erotic'],
            'duration': 270,
            'age_limit': 18,
        }
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')

        webpage = self._download_webpage(url, video_id)

        video_url = self._html_search_regex(r"video_url\s*:\s*'([^']+)'", webpage, 'video URL')

        title = self._html_search_regex(r'<title>(.*?)</title>', webpage, 'title')
        description = self._html_search_regex(
            r'<div class="description"[^>]*>([^<]+)</div>', webpage, 'description', fatal=False)
        thumbnail = self._html_search_regex(
            r'preview_url\s*:\s*\'(.*?)\'', webpage, 'thumbnail', fatal=False)

        categories = re.findall(
            r'<a href="http://anysex\.com/categories/[^"]+" title="[^"]*">([^<]+)</a>', webpage)

        duration = parse_duration(self._search_regex(
            r'<b>Duration:</b> (?:<q itemprop="duration">)?(\d+:\d+)', webpage, 'duration', fatal=False))
        view_count = int_or_none(self._html_search_regex(
            r'<b>Views:</b> (\d+)', webpage, 'view count', fatal=False))

        return {
            'id': video_id,
            'url': video_url,
            'ext': 'mp4',
            'title': title,
            'description': description,
            'thumbnail': thumbnail,
            'categories': categories,
            'duration': duration,
            'view_count': view_count,
            'age_limit': 18,
        }
