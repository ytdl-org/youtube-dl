from __future__ import unicode_literals

import re

from .common import InfoExtractor

from ..utils import (
    determine_ext,
    decode_packed_codes,
    std_headers,
    ExtractorError,
)


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


class VidtodoIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?(vidtod|vidtodo).me/(?:embed-)?(?P<id>\w+)'
    _TESTS = [{
        'url': 'https://vidtodo.me/4c8rx0tt8ek4',
        'md5': '10a0195a5855df8050bd2a0d6692f7c5',
        'info_dict': {
            'id': '4c8rx0tt8ek4',
            'ext': 'mp4',
            'title': 'Watch 343291981 mp4',
        },
    },]

    def _real_extract(self, url):
        video_id = self._match_id(url)

        std_headers['referer'] = 'https://rg3.github.io/youtube-dl/'
        webpage = self._download_webpage('http://vidtod.me/%s' % video_id, video_id, headers=std_headers)

        title = self._html_search_regex(r'<title>(.+?)</title>', webpage, 'title')

        data = re.search(r"}\('.+.split\('\|'\)", webpage).group(0)

        if data:
            codes = decode_packed_codes(data)
        else:
            raise ExtractorError('File not found', expected=True, video_id=video_id)

        source = re.search(r'\.setup\((.+?\],image:.+?\")', codes).group(1) + '}'
        source_keys = ['sources', 'file', 'label', 'image']
        for key_ in source_keys:
            source = source.replace(key_, '"' + key_ + '"')
        source = eval(source)

        formats = []
        for format_ in source['sources']:
            ext = determine_ext(format_['file'], default_ext=None)
            formats.append({
                'url': format_['file'],
                'ext': ext or 'mp4',
                'resolution': format_['label']
            })

        return {
            'id': video_id,
            'title': title,
            'thumbnail': source['image'],
            'formats': formats,
        }
