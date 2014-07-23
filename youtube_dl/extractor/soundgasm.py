# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor


class SoundgasmIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?soundgasm\.net/u/(?P<user>[0-9a-zA-Z_\-]+)/(?P<title>[0-9a-zA-Z_\-]+)'
    _TEST = {
        'url': 'http://soundgasm.net/u/ytdl/Piano-sample',
        'md5': '010082a2c802c5275bb00030743e75ad',
        'info_dict': {
            'id': '88abd86ea000cafe98f96321b23cc1206cbcbcc9',
            'ext': 'm4a',
            'title': 'ytdl_Piano-sample',
            'description': 'Royalty Free Sample Music'
        }
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        display_id = mobj.group('title')
        audio_title = mobj.group('user') + '_' + mobj.group('title')
        webpage = self._download_webpage(url, display_id)
        audio_url = self._html_search_regex(
            r'(?s)m4a\:\s"([^"]+)"', webpage, 'audio URL')
        audio_id = re.split('\/|\.', audio_url)[-2]
        description = self._html_search_regex(
            r'(?s)<li>Description:\s(.*?)<\/li>', webpage, 'description',
            fatal=False)

        return {
            'id': audio_id,
            'display_id': display_id,
            'url': audio_url,
            'title': audio_title,
            'description': description
        }
