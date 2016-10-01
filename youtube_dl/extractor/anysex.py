from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    get_element_by_attribute,
    get_element_by_class,
    int_or_none,
    parse_duration,
    js_to_json,
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
            'thumbnail': 're:^https?://.*\.jpg$',
            'categories': ['Erotic'],
            'duration': 270,
            'age_limit': 18,
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        video_data = self._parse_json(self._search_regex(
            r'var\s+flashvars\s*=\s*({[^}]+});', webpage, 'video data'),
        video_id, transform_source=js_to_json)

        video_url = video_data['video_url']
        title = self._html_search_regex(r'<title>(.*?)</title>', webpage, 'title')

        categories = re.findall(
            r'<a href="http://anysex\.com/categories/[^"]+" title="[^"]*">([^<]+)</a>', webpage)

        duration = parse_duration(get_element_by_attribute('itemprop', 'duration', webpage))
        view_count = int_or_none(self._html_search_regex(
            r'<b>Views:</b> (\d+)', webpage, 'view count', fatal=False))

        return {
            'id': video_id,
            'url': video_url,
            'ext': 'mp4',
            'title': title,
            'description': get_element_by_class('description', webpage),
            'thumbnail': video_data.get('preview_url'),
            'categories': categories,
            'duration': duration,
            'view_count': view_count,
            'age_limit': 18,
        }
