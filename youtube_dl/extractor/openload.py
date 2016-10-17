# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..compat import compat_chr
from ..utils import (
    determine_ext,
    encode_base_n,
    ExtractorError,
    mimetype2ext,
)


class OpenloadIE(InfoExtractor):
    _VALID_URL = r'https://openload.(?:co|io)/(?:f|embed)/(?P<id>[a-zA-Z0-9-]+)'

    _TESTS = [{
        'url': 'https://openload.co/f/kUEfGclsU9o',
        'md5': 'bf1c059b004ebc7a256f89408e65c36e',
        'info_dict': {
            'id': 'kUEfGclsU9o',
            'ext': 'mp4',
            'title': 'skyrim_no-audio_1080.mp4',
            'thumbnail': 're:^https?://.*\.jpg$',
        },
    }, {
        'url': 'https://openload.co/embed/kUEfGclsU9o/skyrim_no-audio_1080.mp4',
        'only_matching': True,
    }, {
        'url': 'https://openload.io/f/ZAn6oz-VZGE/',
        'only_matching': True,
    }, {
        # unavailable via https://openload.co/f/Sxz5sADo82g/, different layout
        # for title and ext
        'url': 'https://openload.co/embed/Sxz5sADo82g/',
        'only_matching': True,
    }]

    @staticmethod
    def openload_level2_debase(m):
        radix, num = int(m.group(1)) + 27, int(m.group(2))
        return '"' + encode_base_n(num, radix) + '"'

    @classmethod
    def openload_level2(cls, txt):
        # The function name is ǃ \u01c3
        # Using escaped unicode literals does not work in Python 3.2
        return re.sub(r'ǃ\((\d+),(\d+)\)', cls.openload_level2_debase, txt, re.UNICODE).replace('"+"', '')

    # Openload uses a variant of aadecode
    # openload_decode and related functions are originally written by
    # vitas@matfyz.cz and released with public domain
    # See https://github.com/rg3/youtube-dl/issues/8489
    @classmethod
    def openload_decode(cls, txt):
        symbol_table = [
            ('_', '(ﾟДﾟ) [ﾟΘﾟ]'),
            ('a', '(ﾟДﾟ) [ﾟωﾟﾉ]'),
            ('b', '(ﾟДﾟ) [ﾟΘﾟﾉ]'),
            ('c', '(ﾟДﾟ) [\'c\']'),
            ('d', '(ﾟДﾟ) [ﾟｰﾟﾉ]'),
            ('e', '(ﾟДﾟ) [ﾟДﾟﾉ]'),
            ('f', '(ﾟДﾟ) [1]'),

            ('o', '(ﾟДﾟ) [\'o\']'),
            ('u', '(oﾟｰﾟo)'),
            ('c', '(ﾟДﾟ) [\'c\']'),

            ('7', '((ﾟｰﾟ) + (o^_^o))'),
            ('6', '((o^_^o) +(o^_^o) +(c^_^o))'),
            ('5', '((ﾟｰﾟ) + (ﾟΘﾟ))'),
            ('4', '(-~3)'),
            ('3', '(-~-~1)'),
            ('2', '(-~1)'),
            ('1', '(-~0)'),
            ('0', '((c^_^o)-(c^_^o))'),
        ]
        delim = '(ﾟДﾟ)[ﾟεﾟ]+'
        ret = ''
        for aachar in txt.split(delim):
            for val, pat in symbol_table:
                aachar = aachar.replace(pat, val)
            aachar = aachar.replace('+ ', '')
            m = re.match(r'^\d+', aachar)
            if m:
                ret += compat_chr(int(m.group(0), 8))
            else:
                m = re.match(r'^u([\da-f]+)', aachar)
                if m:
                    ret += compat_chr(int(m.group(1), 16))
        return cls.openload_level2(ret)

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        if 'File not found' in webpage:
            raise ExtractorError('File not found', expected=True)

        code = self._search_regex(
            r'</video>\s*</div>\s*<script[^>]+>([^<]+)</script>',
            webpage, 'JS code')

        decoded = self.openload_decode(code)

        video_url = self._search_regex(
            r'return\s+"(https?://[^"]+)"', decoded, 'video URL')

        title = self._og_search_title(webpage, default=None) or self._search_regex(
            r'<span[^>]+class=["\']title["\'][^>]*>([^<]+)', webpage,
            'title', default=None) or self._html_search_meta(
            'description', webpage, 'title', fatal=True)

        ext = mimetype2ext(self._search_regex(
            r'window\.vt\s*=\s*(["\'])(?P<mimetype>.+?)\1', decoded,
            'mimetype', default=None, group='mimetype')) or determine_ext(
            video_url, 'mp4')

        return {
            'id': video_id,
            'title': title,
            'ext': ext,
            'thumbnail': self._og_search_thumbnail(webpage, default=None),
            'url': video_url,
        }
