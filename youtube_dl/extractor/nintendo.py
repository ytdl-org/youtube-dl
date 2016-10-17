# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from .ooyala import OoyalaIE
from ..utils import unescapeHTML


class NintendoIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?nintendo\.com/games/detail/(?P<id>[^/?#&]+)'
    _TESTS = [{
        'url': 'http://www.nintendo.com/games/detail/yEiAzhU2eQI1KZ7wOHhngFoAHc1FpHwj',
        'info_dict': {
            'id': 'MzMmticjp0VPzO3CCj4rmFOuohEuEWoW',
            'ext': 'flv',
            'title': 'Duck Hunt Wii U VC NES - Trailer',
            'duration': 60.326,
        },
        'params': {
            'skip_download': True,
        },
        'add_ie': ['Ooyala'],
    }, {
        'url': 'http://www.nintendo.com/games/detail/tokyo-mirage-sessions-fe-wii-u',
        'info_dict': {
            'id': 'tokyo-mirage-sessions-fe-wii-u',
            'title': 'Tokyo Mirage Sessions ♯FE',
        },
        'playlist_count': 3,
    }]

    def _real_extract(self, url):
        page_id = self._match_id(url)

        webpage = self._download_webpage(url, page_id)

        entries = [
            OoyalaIE._build_url_result(m.group('code'))
            for m in re.finditer(
                r'class=(["\'])embed-video\1[^>]+data-video-code=(["\'])(?P<code>(?:(?!\2).)+)\2',
                webpage)]

        return self.playlist_result(
            entries, page_id, unescapeHTML(self._og_search_title(webpage, fatal=False)))
