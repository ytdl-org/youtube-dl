# coding: utf-8
from __future__ import unicode_literals
from youtube_dl.utils import decode_packed_codes

from .common import InfoExtractor


class SendFoxIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?sendfox\.org/(?P<id>[0-9a-z]+)'
    _TEST = {
        'url': 'https://sendfox.org/bsw8k32fezg6/big_buck_bunny_1080p_surround.avi',
        'md5': 'a1a3969c928f8c3850d34abc18c33cc6',
        'info_dict': {
            'id': 'bsw8k32fezg6',
            'ext': 'mp4',
            'title': 'big buck bunny 1080p surround',
            'thumbnail': 'https://img.sendfox.org/bsw8k32fezg6_t.jpg'
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        packed_code = self._search_regex(
            r'(eval\(function\(p,a,c,k,e,d\){.+)', webpage, 'obfuscated code')

        video_src = self._search_regex(
            r'src:"(.+?)"', decode_packed_codes(packed_code), 'src')

        return {
            'id': video_id,
            'title': self._html_search_regex(r'<h6 class="card-title">(.+?)</h6>', webpage, 'title'),
            'formats': self._extract_m3u8_formats(video_src, video_id, ext='mp4'),
            'thumbnail': 'https://img.sendfox.org/' + video_id + '_t.jpg',
            'ext': 'mp4'
        }
