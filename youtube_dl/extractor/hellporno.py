from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    js_to_json,
    remove_end,
    determine_ext,
)


class HellPornoIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?hellporno\.(?:com/videos|net/v)/(?P<id>[^/]+)'
    _TESTS = [{
        'url': 'http://hellporno.com/videos/dixie-is-posing-with-naked-ass-very-erotic/',
        'md5': '1fee339c610d2049699ef2aa699439f1',
        'info_dict': {
            'id': '149116',
            'display_id': 'dixie-is-posing-with-naked-ass-very-erotic',
            'ext': 'mp4',
            'title': 'Dixie is posing with naked ass very erotic',
            'thumbnail': r're:https?://.*\.jpg$',
            'age_limit': 18,
        }
    }, {
        'url': 'http://hellporno.net/v/186271/',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        display_id = self._match_id(url)

        webpage = self._download_webpage(url, display_id)

        title = remove_end(self._html_search_regex(
            r'<title>([^<]+)</title>', webpage, 'title'), ' - Hell Porno')

        flashvars = self._parse_json(self._search_regex(
            r'var\s+flashvars\s*=\s*({.+?});', webpage, 'flashvars'),
            display_id, transform_source=js_to_json)

        video_id = flashvars.get('video_id')
        thumbnail = flashvars.get('preview_url')
        ext = determine_ext(flashvars.get('postfix'), 'mp4')

        formats = []
        for video_url_key in ['video_url', 'video_alt_url']:
            video_url = flashvars.get(video_url_key)
            if not video_url:
                continue
            video_text = flashvars.get('%s_text' % video_url_key)
            fmt = {
                'url': video_url,
                'ext': ext,
                'format_id': video_text,
            }
            m = re.search(r'^(?P<height>\d+)[pP]', video_text)
            if m:
                fmt['height'] = int(m.group('height'))
            formats.append(fmt)
        self._sort_formats(formats)

        categories = self._html_search_meta(
            'keywords', webpage, 'categories', default='').split(',')

        return {
            'id': video_id,
            'display_id': display_id,
            'title': title,
            'thumbnail': thumbnail,
            'categories': categories,
            'age_limit': 18,
            'formats': formats,
        }
