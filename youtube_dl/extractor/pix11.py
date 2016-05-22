# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from .ooyala import OoyalaIE


class Pix11IE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?pix11\.com/\d{4}/(?:\d{2}/){2}(?P<display_id>[a-z0-9-]+)'
    _TEST = {
        'url': 'http://pix11.com/2016/05/05/donald-trump-on-cinco-de-mayo-i-love-hispanics/',
        'info_dict': {
            'id': 'hqbXBiMzE6O3im1B98VpANYppaJMcuY9',
            'ext': 'mp4',
            'title': 'Donald Trump on Cinco de Mayo: `I love Hispanics!`',
            'duration': 53.62,
        },
        'params': {
            # m3u8 download
            'skip_download': True,
        }
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        display_id = mobj.group('display_id')
        webpage = self._download_webpage(url, display_id)
        
        return OoyalaIE._build_url_result(self._search_regex(
            r'"ooyalaplayer-1",\s*"(\w{32})"', webpage, 'ooyala id'))
