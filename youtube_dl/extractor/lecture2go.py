# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import determine_ext


class Lecture2GoIE(InfoExtractor):
    _VALID_URL = r'https?://lecture2go\.uni-hamburg\.de/veranstaltungen/-/v/(?P<id>\d+)'
    _TEST = {
        'url': 'https://lecture2go.uni-hamburg.de/veranstaltungen/-/v/17473',
        'md5': 'a9e76f83b3ef58019c4b7dbc35f406c1',
        'info_dict': {
            'id': '17473',
            'ext': 'mp4',
            'url': 'https://fms1.rrz.uni-hamburg.de/abo/64.050_FrankHeitmann_2015-04-13_14-35.mp4',
            'title': '2 - Endliche Automaten und reguläre Sprachen'
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        title = self._html_search_regex(r'<em[^>]+class="title">(.+)</em>', webpage, 'title')

        formats = []
        for url in set(re.findall(r'"src","([^"]+)"', webpage)):
            ext = determine_ext(url)
            if ext == 'f4m':
                formats.extend(self._extract_f4m_formats(url, video_id))
            elif ext == 'm3u8':
                formats.extend(self._extract_m3u8_formats(url, video_id))
            else:
                formats.append({
                    'url': url,
                })

        self._sort_formats(formats)

        creator = self._html_search_regex(r'<div[^>]+id="description">([^<]+)</div>', webpage, 'creator')

        return {
            'id': video_id,
            'title': title,
            'formats': formats,
            'creator': creator
        }
