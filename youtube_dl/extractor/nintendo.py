from __future__ import unicode_literals

from .common import InfoExtractor
from .ooyala import OoyalaIE

import re


class NintendoIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?nintendo\.com/games/detail/(?P<id>[\w-]+)'
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
        },
        'params': {
            'skip_download': True,
        },
        'add_ie': ['Ooyala'],
        'playlist_count': 4,
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        ooyala_codes = re.findall(
            r'data-video-code=(["\'])(?P<code>.+?)\1',
            webpage)

        entries = []
        for ooyala_code in ooyala_codes:
            entries.append(OoyalaIE._build_url_result(ooyala_code[1]))

        return self.playlist_result(entries, video_id, self._og_search_title(webpage))
