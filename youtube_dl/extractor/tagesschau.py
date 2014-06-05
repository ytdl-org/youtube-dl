# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import re
import json

from .common import InfoExtractor


class TagesschauIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?tagesschau\.de/multimedia/video/video(?P<id>-?\d+)\.html'

    _TESTS = [{
        'url': 'http://www.tagesschau.de/multimedia/video/video1399128.html',
        'md5': 'bcdeac2194fb296d599ce7929dfa4009',
        'info_dict': {
            'id': '1399128',
            'ext': 'mp4',
            'title': 'Harald Range, Generalbundesanwalt, zu den Ermittlungen',
            'description': 'md5:69da3c61275b426426d711bde96463ab',
            'thumbnail': 're:^http:.*\.jpg$',
        },
    }, {
        'url': 'http://www.tagesschau.de/multimedia/video/video-196.html',
        'md5': '8aaa8bf3ae1ca2652309718c03019128',
        'info_dict': {
            'id': '196',
            'ext': 'mp4',
            'title': 'Ukraine-Konflikt: Klitschko in Kiew als B\xfcrgermeister vereidigt',
            'description': 'md5:f22e4af75821d174fa6c977349682691',
            'thumbnail': 're:http://.*\.jpg',
        },
    }]      

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')

        if video_id.startswith('-'):
            display_id = video_id.strip('-')
        else:
            display_id = video_id

        webpage = self._download_webpage(url, display_id)

        playerpage = self._download_webpage(
            'http://www.tagesschau.de/multimedia/video/video%s~player_autoplay-true.html' % video_id, display_id)

        medias = re.findall(r'"(http://media.+?)", type:"video/(.+?)", quality:"(.+?)"', playerpage)

        formats = []
        for url, ext, res in medias:
            
            if res == 's':
                res = 'small'
                quality = 0
            elif res == 'm':
                res = 'medium'
                quality = 1
            elif res == 'l':
                res = 'large'
                quality = 2

            formats.append({
                'format_id': res+'_'+ext,
                'url': url,
                'quality': quality,
                'ext': ext,
            })

        self._sort_formats(formats)

        thumbnail = re.findall(r'"(/multimedia/.+?\.jpg)"', playerpage)[-1]

        return {
            'id': display_id,
            'title': self._og_search_title(webpage).strip(),
            'thumbnail': 'http://www.tagesschau.de'+thumbnail,
            'formats': formats,
            'description': self._og_search_description(webpage).strip(),
        }
