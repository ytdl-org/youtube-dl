# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..compat import compat_chr
from ..utils import (
    determine_ext,
    ExtractorError,
)


class OpenloadIE(InfoExtractor):
    _VALID_URL = r'https?://(?:openload\.(?:co|io)|oload\.tv)/(?:f|embed)/(?P<id>[a-zA-Z0-9-_]+)'

    _TESTS = [{
        'url': 'https://openload.co/f/kUEfGclsU9o',
        'md5': 'bf1c059b004ebc7a256f89408e65c36e',
        'info_dict': {
            'id': 'kUEfGclsU9o',
            'ext': 'mp4',
            'title': 'skyrim_no-audio_1080.mp4',
            'thumbnail': r're:^https?://.*\.jpg$',
        },
    }, {
        'url': 'https://openload.co/embed/rjC09fkPLYs',
        'info_dict': {
            'id': 'rjC09fkPLYs',
            'ext': 'mp4',
            'title': 'movie.mp4',
            'thumbnail': r're:^https?://.*\.jpg$',
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
    }, {
        'url': 'https://oload.tv/embed/KnG-kKZdcfY/',
        'only_matching': True,
    }]

    @staticmethod
    def _extract_urls(webpage):
        return re.findall(
            r'<iframe[^>]+src=["\']((?:https?://)?(?:openload\.(?:co|io)|oload\.tv)/embed/[a-zA-Z0-9-_]+)',
            webpage)

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage('https://openload.co/embed/%s/' % video_id, video_id)

        if 'File not found' in webpage or 'deleted by the owner' in webpage:
            raise ExtractorError('File not found', expected=True)

        ol_id = self._search_regex(
            '<span[^>]+id="[^"]+"[^>]*>([0-9A-Za-z]+)</span>',
            webpage, 'openload ID')

        video_url_chars = []

        first_char = ord(ol_id[0])
        key = first_char - 55
        maxKey = max(2, key)
        key = min(maxKey, len(ol_id) - 38)
        t = ol_id[key:key + 36]

        hashMap = {}
        v = ol_id.replace(t, '')
        h = 0

        while h < len(t):
            f = t[h:h + 3]
            i = int(f, 8)
            hashMap[h / 3] = i
            h += 3

        h = 0
        H = 0
        while h < len(v):
            B = ''
            C = ''
            if len(v) >= h + 2:
                B = v[h:h + 2]
            if len(v) >= h + 3:
                C = v[h:h + 3]
            i = int(B, 16)
            h += 2
            if H % 3 == 0:
                i = int(C, 8)
                h += 1
            elif H % 2 == 0 and H != 0 and ord(v[H - 1]) < 60:
                i = int(C, 10)
                h += 1
            index = H % 7

            A = hashMap[index]
            i ^= 213
            i ^= A
            video_url_chars.append(compat_chr(i))
            H += 1

        video_url = 'https://openload.co/stream/%s?mime=true'
        video_url = video_url % (''.join(video_url_chars))

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
            'ext': determine_ext(title, 'mp4'),
            'subtitles': subtitles,
        }
        return info_dict
