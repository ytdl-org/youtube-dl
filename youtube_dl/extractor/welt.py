from __future__ import unicode_literals

import re

from .common import InfoExtractor

from ..utils import (
    remove_end,
    int_or_none
)


class WeltIE(InfoExtractor):
    IE_NAME = 'welt.de'
    _VALID_URL = r'''https?://(?:www\.)?welt\.de/[^\.]+/(?P<id>[a-z]+\d+)(?:/.*)?'''
    _TESTS = [
        {
            # All videos have a predefined lifetime, usually just 30-45 days
            'url': 'https://www.welt.de/mediathek/dokumentation/natur-und-wildlife/sendung157940018/Mega-Croc-vs-Superschlange.html',
            'info_dict': {
                'id': 'sendung157940018',
                'ext': 'mp4',
                'title': 'Mega Croc vs. Superschlange',
            }
        }
    ]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)
        title = remove_end(self._html_search_regex(r'<title>([^<]+)</title>', webpage, 'title')
                           .strip(), ' - Video - WELT')

        sources = self._search_regex(r'(["\'])?sources\1\s*:\s*\[({\s*\1file\1\s*:\s*\1([^\1,])+\1\s*}\s*,?)+', webpage, 'sources', group=0)
        files = re.findall(r'http[^\'"]+', sources)

        formats = []
        for url in files:
            number = re.search(r'_(\d+)\.mp4', url).group(1)
            formats.append({
                'url': url,
                'quality_key': int_or_none(number)
            })
        self._remove_duplicate_formats(formats)
        formats = sorted(formats, key=lambda x: x['quality_key'])
        quality_counter = -1
        for i in range(len(formats) - 1, 0, -1):
            formats[i] = {'url': formats[i]['url'], 'quality': quality_counter}
            quality_counter -= 1

        return {
            'id': video_id,
            'ext': 'mp4',
            'title': title,
            'formats': formats
        }
