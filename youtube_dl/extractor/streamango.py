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
        video_id = self._match_id(url)

        webpage = self._download_webpage(url, video_id)

        title = self._og_search_title(webpage, default=video_id)

        formats = []
        for format_ in re.findall(r'({[^}]*\bsrc\s*:\s*[^}]*})', webpage):
            video = self._parse_json(
                format_, video_id, transform_source=js_to_json, fatal=False)
            if not video:
                continue
            src = video.get('src')
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
        self._sort_formats(formats)

        return {
            'id': video_id,
            'url': url,
            'title': title,
            'formats': formats,
        }
