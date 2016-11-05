# coding: utf-8
from __future__ import unicode_literals, division

import re

from .common import InfoExtractor
from ..compat import (
    compat_chr,
    compat_ord,
)
from ..utils import (
    determine_ext,
    ExtractorError,
)
from ..jsinterp import (
    JSInterpreter,
    _NAME_RE
)


class OpenloadIE(InfoExtractor):
    _VALID_URL = r'https?://openload\.(?:co|io)/(?:f|embed)/(?P<id>[a-zA-Z0-9-_]+)'

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
        'url': 'https://openload.co/embed/rjC09fkPLYs',
        'info_dict': {
            'id': 'rjC09fkPLYs',
            'ext': 'mp4',
            'title': 'movie.mp4',
            'thumbnail': 're:^https?://.*\.jpg$',
            'subtitles': {
                'en': [{
                    'ext': 'vtt',
                }],
            },
        },
        'params': {
            'skip_download': True,  # test subtitles only
        },
    }, {
        'url': 'https://openload.co/embed/kUEfGclsU9o/skyrim_no-audio_1080.mp4',
        'only_matching': True,
    }, {
        'url': 'https://openload.io/f/ZAn6oz-VZGE/',
        'only_matching': True,
    }, {
        'url': 'https://openload.co/f/_-ztPaZtMhM/',
        'only_matching': True,
    }, {
        # unavailable via https://openload.co/f/Sxz5sADo82g/, different layout
        # for title and ext
        'url': 'https://openload.co/embed/Sxz5sADo82g/',
        'only_matching': True,
    }]

    def openload_decode(self, txt):
        symbol_dict = {
            '(ﾟДﾟ) [ﾟΘﾟ]': '_',
            '(ﾟДﾟ) [ﾟωﾟﾉ]': 'a',
            '(ﾟДﾟ) [ﾟΘﾟﾉ]': 'b',
            '(ﾟДﾟ) [\'c\']': 'c',
            '(ﾟДﾟ) [ﾟｰﾟﾉ]': 'd',
            '(ﾟДﾟ) [ﾟДﾟﾉ]': 'e',
            '(ﾟДﾟ) [1]': 'f',
            '(ﾟДﾟ) [\'o\']': 'o',
            '(oﾟｰﾟo)': 'u',
            '(ﾟДﾟ) [\'c\']': 'c',
            '((ﾟｰﾟ) + (o^_^o))': '7',
            '((o^_^o) +(o^_^o) +(c^_^o))': '6',
            '((ﾟｰﾟ) + (ﾟΘﾟ))': '5',
            '(-~3)': '4',
            '(-~-~1)': '3',
            '(-~1)': '2',
            '(-~0)': '1',
            '((c^_^o)-(c^_^o))': '0',
        }
        delim = '(ﾟДﾟ)[ﾟεﾟ]+'
        end_token = '(ﾟДﾟ)[ﾟoﾟ]'
        symbols = '|'.join(map(re.escape, symbol_dict.keys()))
        txt = re.sub('(%s)\+\s?' % symbols, lambda m: symbol_dict[m.group(1)], txt)
        ret = ''
        for aacode in re.findall(r'{0}\+\s?{1}(.*?){0}'.format(re.escape(end_token), re.escape(delim)), txt):
            for aachar in aacode.split(delim):
                if aachar.isdigit():
                    ret += compat_chr(int(aachar, 8))
                else:
                    m = re.match(r'^u([\da-f]{4})$', aachar)
                    if m:
                        ret += compat_chr(int(m.group(1), 16))
                    else:
                        self.report_warning("Cannot decode: %s" % aachar)
        return ret

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage('https://openload.co/embed/%s/' % video_id, video_id)

        if 'File not found' in webpage or 'deleted by the owner' in webpage:
            raise ExtractorError('File not found', expected=True)

        # The following decryption algorithm is written by @yokrysty and
        # declared to be freely used in youtube-dl
        # See https://github.com/rg3/youtube-dl/issues/10408
        enc_data = self._html_search_regex(
            r'<span[^>]*>([^<]+)</span>\s*<span[^>]*>[^<]+</span>\s*<span[^>]+id="streamurl"',
            webpage, 'encrypted data')

        enc_code = self._html_search_regex(r'<script[^>]+>(ﾟωﾟ[^<]+)</script>',
                                           webpage, 'encrypted code')

        js_code = self.openload_decode(enc_code)
        jsi = JSInterpreter(js_code)

        m_offset_fun = self._search_regex(r'slice\(0\s*-\s*(%s)\(\)' % _NAME_RE, js_code, 'javascript offset function')
        m_diff_fun = self._search_regex(r'charCodeAt\(0\)\s*\+\s*(%s)\(\)' % _NAME_RE, js_code, 'javascript diff function')

        offset = jsi.call_function(m_offset_fun)
        diff = jsi.call_function(m_diff_fun)

        video_url_chars = []

        for idx, c in enumerate(enc_data):
            j = compat_ord(c)
            if j >= 33 and j <= 126:
                j = ((j + 14) % 94) + 33
            if idx == len(enc_data) - offset:
                j += diff
            video_url_chars += compat_chr(j)

        video_url = 'https://openload.co/stream/%s?mime=true' % ''.join(video_url_chars)

        title = self._og_search_title(webpage, default=None) or self._search_regex(
            r'<span[^>]+class=["\']title["\'][^>]*>([^<]+)', webpage,
            'title', default=None) or self._html_search_meta(
            'description', webpage, 'title', fatal=True)

        entries = self._parse_html5_media_entries(url, webpage, video_id)
        subtitles = entries[0]['subtitles'] if entries else None

        info_dict = {
            'id': video_id,
            'title': title,
            'thumbnail': self._og_search_thumbnail(webpage, default=None),
            'url': video_url,
            # Seems all videos have extensions in their titles
            'ext': determine_ext(title),
            'subtitles': subtitles,
        }

        return info_dict
