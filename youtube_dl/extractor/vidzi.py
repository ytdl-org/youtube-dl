# coding: utf-8
from __future__ import unicode_literals

from .jwplatform import JWPlatformBaseIE
from ..utils import (
    decode_packed_codes,
    js_to_json,
)


class VidziIE(JWPlatformBaseIE):
    _VALID_URL = r'https?://(?:www\.)?vidzi\.tv/(?P<id>\w+)'
    _TEST = {
        'url': 'http://vidzi.tv/cghql9yq6emu.html',
        'md5': '4f16c71ca0c8c8635ab6932b5f3f1660',
        'info_dict': {
            'id': 'cghql9yq6emu',
            'ext': 'mp4',
            'title': 'youtube-dl test video  1\\\\2\'3/4<5\\\\6ä7↭',
        },
        'params': {
            # m3u8 download
            'skip_download': True,
        },
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)

        webpage = self._download_webpage(url, video_id)
        title = self._html_search_regex(
            r'(?s)<h2 class="video-title">(.*?)</h2>', webpage, 'title')

        code = decode_packed_codes(webpage).replace('\\\'', '\'')
        jwplayer_data = self._parse_json(
            self._search_regex(r'setup\(([^)]+)\)', code, 'jwplayer data'),
            video_id, transform_source=js_to_json)

        info_dict = self._parse_jwplayer_data(jwplayer_data, video_id, require_title=False)
        info_dict['title'] = title

        return info_dict
