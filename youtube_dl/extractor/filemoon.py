# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from .. import utils
from ..utils import js_to_json


class FileMoonIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?filemoon\.sx/./(?P<id>\w+)(/(?P<title>.*))*'
    _TEST = {
        'url': 'https://filemoon.sx/e/dw40rxrzruqz',
        'md5': '5a713742f57ac4aef29b74733e8dda01',
        'info_dict': {
            'id': 'dw40rxrzruqz',
            'title': 'dw40rxrzruqz',
            'ext': 'mp4'
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        m = self._VALID_URL_RE.match(url)
        title = m.group('title')
        if not title:
            title = video_id

        webpage = self._download_webpage(url, video_id)
        matches = re.findall(r'(eval.*?)<\/script>', webpage, flags=re.DOTALL)
        packed = matches[-1]
        unpacked = utils.decode_packed_codes(packed)
        jwplayer_sources = self._parse_json(
            self._search_regex(
                r"(?s)player\.setup\(\{sources:(.*?])", unpacked, 'jwplayer sources'),
            video_id, transform_source=js_to_json)

        formats = self._parse_jwplayer_formats(jwplayer_sources, video_id)

        return {
            'id': video_id,
            'title': title,
            'formats': formats
        }
