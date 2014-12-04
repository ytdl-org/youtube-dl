# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..compat import (
    compat_chr,
    compat_ord,
)
from ..utils import (
    int_or_none,
    parse_filesize,
)


class XMinusIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?x-minus\.org/track/(?P<id>[0-9]+)'
    _TEST = {
        'url': 'http://x-minus.org/track/4542/%D0%BF%D0%B5%D1%81%D0%B5%D0%BD%D0%BA%D0%B0-%D1%88%D0%BE%D1%84%D0%B5%D1%80%D0%B0.html',
        'md5': '401a15f2d2dcf6d592cb95528d72a2a8',
        'info_dict': {
            'id': '4542',
            'ext': 'mp3',
            'title': 'Леонид Агутин-Песенка шофера',
            'duration': 156,
            'tbr': 320,
            'filesize_approx': 5900000,
            'view_count': int,
            'description': 'md5:03238c5b663810bc79cf42ef3c03e371',
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        artist = self._html_search_regex(
            r'minus_track\.artist="(.+?)"', webpage, 'artist')
        title = artist + '-' + self._html_search_regex(
            r'minus_track\.title="(.+?)"', webpage, 'title')
        duration = int_or_none(self._html_search_regex(
            r'minus_track\.dur_sec=\'([0-9]*?)\'',
            webpage, 'duration', fatal=False))
        filesize_approx = parse_filesize(self._html_search_regex(
            r'<div class="filesize[^"]*"></div>\s*([0-9.]+\s*[a-zA-Z][bB])',
            webpage, 'approximate filesize', fatal=False))
        tbr = int_or_none(self._html_search_regex(
            r'<div class="quality[^"]*"></div>\s*([0-9]+)\s*kbps',
            webpage, 'bitrate', fatal=False))
        view_count = int_or_none(self._html_search_regex(
            r'<div class="quality.*?► ([0-9]+)',
            webpage, 'view count', fatal=False))
        description = self._html_search_regex(
            r'(?s)<div id="song_texts">(.*?)</div><br',
            webpage, 'song lyrics', fatal=False)
        if description:
            description = re.sub(' *\r *', '\n', description)

        enc_token = self._html_search_regex(
            r'minus_track\.tkn="(.+?)"', webpage, 'enc_token')
        token = ''.join(
            c if pos == 3 else compat_chr(compat_ord(c) - 1)
            for pos, c in enumerate(reversed(enc_token)))
        video_url = 'http://x-minus.org/dwlf/%s/%s.mp3' % (video_id, token)

        return {
            'id': video_id,
            'title': title,
            'url': video_url,
            'duration': duration,
            'filesize_approx': filesize_approx,
            'tbr': tbr,
            'view_count': view_count,
            'description': description,
        }
