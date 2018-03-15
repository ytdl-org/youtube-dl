from __future__ import unicode_literals

import re

from .common import InfoExtractor

from ..utils import (
    decode_packed_codes,
    ExtractorError,
    js_to_json,
)


class VidtodoIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?(vidtod|vidtodo).me/(?:embed-)?(?P<id>\w+)'
    _TESTS = [{
        'url': 'https://vidtodo.me/4c8rx0tt8ek4',
        'md5': 'cfd8415e586d59a4de942757eeb7145f',
        'info_dict': {
            'id': '4c8rx0tt8ek4',
            'ext': 'mp4',
            'title': 'Watch 343291981 mp4',
        },
    }, ]
    _USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36'

    @staticmethod
    def xpro(encoded_url):
        decoded_url = ''
        alphabet = 'abcdefghijklmnopqrstuvwxyz'
        betalpha = 'nopqrstuvwxyzabcdefghijklm'
        for char in encoded_url:
            if char.isalpha():
                decoded_url += alphabet[betalpha.find(char)]
            else:
                decoded_url += char
        return decoded_url

    def _real_extract(self, url):
        video_id = self._match_id(url)

        headers = {
            'User-Agent': self._USER_AGENT,
            'Connection': 'keep-alive',
            'referer': 'https://vidtodo.com',
        }

        webpage = self._download_webpage('http://vidtod.me/%s' % video_id, video_id, headers=headers)

        title = self._html_search_regex(r'<title>(.+?)</title>', webpage, 'title')

        data = re.search(r"}\('.+\.split\('\|'\)", webpage).group(0)
        if data:
            codes = decode_packed_codes(data)
        else:
            raise ExtractorError('File not found', expected=True, video_id=video_id)

        source = self._search_regex(r'setup\(([^)].+\.jpg\")', codes, 'jwplayer data', fatal=False) + '}'
        encoded_url = self._search_regex(r'xpro\((.+?)\)', source, 'encoded url', fatal=False)
        if encoded_url:
            source = source.replace('xpro(' + encoded_url + ')', self.xpro(encoded_url))

        jwplayer_data = self._parse_json(source, video_id, transform_source=js_to_json)

        info_dict = self._parse_jwplayer_data(jwplayer_data, video_id, require_title=False)
        info_dict['title'] = title

        return info_dict
