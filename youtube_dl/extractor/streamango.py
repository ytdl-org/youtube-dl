# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..compat import compat_chr
from ..utils import (
    determine_ext,
    ExtractorError,
    int_or_none,
    js_to_json,
)


class StreamangoIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?(?:streamango\.com|fruithosts\.net)/(?:f|embed)/(?P<id>[^/?#&]+)'
    _TESTS = [{
        'url': 'https://streamango.com/f/clapasobsptpkdfe/20170315_150006_mp4',
        'md5': 'e992787515a182f55e38fc97588d802a',
        'info_dict': {
            'id': 'clapasobsptpkdfe',
            'ext': 'mp4',
            'title': '20170315_150006.mp4',
        }
    }, {
        # no og:title
        'url': 'https://streamango.com/embed/foqebrpftarclpob/asdf_asd_2_mp4',
        'info_dict': {
            'id': 'foqebrpftarclpob',
            'ext': 'mp4',
            'title': 'foqebrpftarclpob',
        },
        'params': {
            'skip_download': True,
        },
        'skip': 'gone',
    }, {
        'url': 'https://streamango.com/embed/clapasobsptpkdfe/20170315_150006_mp4',
        'only_matching': True,
    }, {
        'url': 'https://fruithosts.net/f/mreodparcdcmspsm/w1f1_r4lph_2018_brrs_720p_latino_mp4',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        def decrypt_src(encoded, val):
            ALPHABET = '=/+9876543210zyxwvutsrqponmlkjihgfedcbaZYXWVUTSRQPONMLKJIHGFEDCBA'
            encoded = re.sub(r'[^A-Za-z0-9+/=]', '', encoded)
            decoded = ''
            sm = [None] * 4
            i = 0
            str_len = len(encoded)
            while i < str_len:
                for j in range(4):
                    sm[j % 4] = ALPHABET.index(encoded[i])
                    i += 1
                char_code = ((sm[0] << 0x2) | (sm[1] >> 0x4)) ^ val
                decoded += compat_chr(char_code)
                if sm[2] != 0x40:
                    char_code = ((sm[1] & 0xf) << 0x4) | (sm[2] >> 0x2)
                    decoded += compat_chr(char_code)
                if sm[3] != 0x40:
                    char_code = ((sm[2] & 0x3) << 0x6) | sm[3]
                    decoded += compat_chr(char_code)
            return decoded

        video_id = self._match_id(url)

        webpage = self._download_webpage(url, video_id)

        title = self._og_search_title(webpage, default=video_id)

        formats = []
        for format_ in re.findall(r'({[^}]*\bsrc\s*:\s*[^}]*})', webpage):
            mobj = re.search(r'(src\s*:\s*[^(]+\(([^)]*)\)[\s,]*)', format_)
            if mobj is None:
                continue

            format_ = format_.replace(mobj.group(0), '')

            video = self._parse_json(
                format_, video_id, transform_source=js_to_json,
                fatal=False) or {}

            mobj = re.search(
                r'([\'"])(?P<src>(?:(?!\1).)+)\1\s*,\s*(?P<val>\d+)',
                mobj.group(1))
            if mobj is None:
                continue

            src = decrypt_src(mobj.group('src'), int_or_none(mobj.group('val')))
            if not src:
                continue

            ext = determine_ext(src, default_ext=None)
            if video.get('type') == 'application/dash+xml' or ext == 'mpd':
                formats.extend(self._extract_mpd_formats(
                    src, video_id, mpd_id='dash', fatal=False))
            else:
                formats.append({
                    'url': src,
                    'ext': ext or 'mp4',
                    'width': int_or_none(video.get('width')),
                    'height': int_or_none(video.get('height')),
                    'tbr': int_or_none(video.get('bitrate')),
                })

        if not formats:
            error = self._search_regex(
                r'<p[^>]+\bclass=["\']lead[^>]+>(.+?)</p>', webpage,
                'error', default=None)
            if not error and '>Sorry' in webpage:
                error = 'Video %s is not available' % video_id
            if error:
                raise ExtractorError(error, expected=True)

        self._sort_formats(formats)

        return {
            'id': video_id,
            'url': url,
            'title': title,
            'formats': formats,
        }
