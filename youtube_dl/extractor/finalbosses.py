# coding: utf-8
from __future__ import unicode_literals

import re
from .common import InfoExtractor

from ..utils import unescapeHTML


class FinalBossesIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?finalbosses\.com/(?P<display_id>[a-z-]+)'
    _TEST = {
        'url': 'http://finalbosses.com/playing-with-sacks-golden-axe',
        'info_dict': {
            'id': 'TL2iCGym',
            'ext': 'mp4',
            'title': 'Playing With Sacks - Golden Axe - Final Bosses',
            'description': 'md5:8ece97844ce7fd3640d8536bc65c1c61',
            'thumbnail': 'http://finalbosses.com/wp-content/uploads/2015/06/Playingwithsacks-GoldenAxe.png',
        },
        'params': {
            'skip_download': True,
        }
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        display_id = mobj.group('display_id')

        webpage = self._download_webpage(url, display_id)

        video_id = self._search_regex(
            r'content.jwplatform.com/players/(?P<id>\w+)-.+.js',
            webpage, 'video id')

        formats = self._extract_m3u8_formats(
            'http://content.jwplatform.com/manifests/%s.m3u8' % video_id,
            display_id, 'mp4')

        return {
            'id': video_id,
            'title': self._og_search_title(webpage),
            'description': unescapeHTML(self._og_search_description(webpage)),
            'thumbnail': self._og_search_thumbnail(webpage),
            'formats': formats,
        }
