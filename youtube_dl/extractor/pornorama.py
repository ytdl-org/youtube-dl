from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..compat import compat_urllib_parse_unquote
from ..utils import (
    clean_html,
    ExtractorError
)


class PornoramaIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?pornorama\.com/video(?P<id>[0-9]+)(?:.*)'
    _TEST = {
        'url': 'http://www.pornorama.com/video1416287/amy_my_neighbor_fucked',
        'md5': '',
        'info_dict': {
            'id': '1416287',
            'ext': 'flv',
            'title': 'amy_my_neighbor_fucked',
            'age_limit': 18,
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        video_url = compat_urllib_parse_unquote(
            self._search_regex(r'flv_url=(.+?)&', webpage, 'video URL'))
        video_title = self._html_search_regex(
            r'<title>(.*?)\s+-\s+PORNORAMA', webpage, 'title')
        video_thumbnail = self._search_regex(
            r'url_bigthumb=(.+?)&amp', webpage, 'thumbnail', fatal=False)

        formats = [{
            'url': video_url,
        }]

        self._sort_formats(formats)

        return {
            'id': video_id,
            'formats': formats,
            'title': video_title,
            'ext': 'flv',
            'thumbnail': video_thumbnail,
            'age_limit': 18,
        }
