# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    determine_ext,
    int_or_none,
    js_to_json,
)


class StreamangoIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?streamango\.com/(?:f|embed)/(?P<id>[^/?#&]+)'
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
    }, {
        'url': 'https://streamango.com/embed/clapasobsptpkdfe/20170315_150006_mp4',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        def decrypt_src(str_, val):
            k = '=/+9876543210zyxwvutsrqponmlkjihgfedcbaZYXWVUTSRQPONMLKJIHGFEDCBA'
            str_ = re.sub(r'[^A-Za-z0-9+/=]', '', str_)
            src = ''
            sm = [None] * 4
            i = 0
            str_len = len(str_)
            while i < str_len:
                for j in range(4):
                    sm[j % 4] = k.index(str_[i])
                    i += 1
                charCode = ((sm[0] << 0x2) | (sm[1] >> 0x4)) ^ val
                src += chr(charCode)
                if (sm[2] != 0x40):
                    charCode = ((sm[1] & 0xf) << 0x4) | (sm[2] >> 0x2)
                    src += chr(charCode)
                if (sm[3] != 0x40):
                    charCode = ((sm[2] & 0x3) << 0x6) | sm[3]
                    src += chr(charCode)
            return src

        video_id = self._match_id(url)

        webpage = self._download_webpage(url, video_id)

        title = self._og_search_title(webpage, default=video_id)

        formats = []
        for format_ in re.findall(r'\(\s*({[^}]*\bsrc\s*:\s*[^}]*})', webpage):
            mobj = re.search(r'(src\s*:\s*[^(]\(([^)]*)\)[\s,]*)', format_)
            if mobj is None:
                continue
            format_ = format_.replace(mobj.group(0), '')

            video = self._parse_json(
                format_, video_id, transform_source=js_to_json, fatal=False)
            if not video:
                continue

            mobj = re.search(r'[\'"](?P<src>[^\'"]+)[\'"]\s*,\s*(?P<val>\d+)', mobj.group(1))
            if mobj is None:
                continue

            src = decrypt_src(mobj.group('src'), int_or_none(mobj.group('val')))
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
        self._sort_formats(formats)

        return {
            'id': video_id,
            'url': url,
            'title': title,
            'formats': formats,
        }
