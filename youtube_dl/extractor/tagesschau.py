# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import re

from .common import InfoExtractor


class TagesschauIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?tagesschau\.de/multimedia/video/video(?P<id>-?[0-9]+)\.html'

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
            'title': 'Ukraine-Konflikt: Klitschko in Kiew als Bürgermeister vereidigt',
            'description': 'md5:f22e4af75821d174fa6c977349682691',
            'thumbnail': 're:http://.*\.jpg',
        },
    }]

    _FORMATS = {
        's': {'width': 256, 'height': 144, 'quality': 1},
        'm': {'width': 512, 'height': 288, 'quality': 2},
        'l': {'width': 960, 'height': 544, 'quality': 3},
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')

        if video_id.startswith('-'):
            display_id = video_id.strip('-')
        else:
            display_id = video_id

        webpage = self._download_webpage(url, display_id)

        playerpage = self._download_webpage(
            'http://www.tagesschau.de/multimedia/video/video%s~player_autoplay-true.html' % video_id,
            display_id, 'Downloading player page')

        medias = re.findall(
            r'"(http://media.+?)", type:"video/(.+?)", quality:"(.+?)"',
            playerpage)

        formats = []
        for url, ext, res in medias:
            f = {
                'format_id': res + '_' + ext,
                'url': url,
                'ext': ext,
            }
            f.update(self._FORMATS.get(res, {}))
            formats.append(f)

        self._sort_formats(formats)

        thumbnail = re.findall(r'"(/multimedia/.+?\.jpg)"', playerpage)[-1]

        return {
            'id': display_id,
            'title': self._og_search_title(webpage).strip(),
            'thumbnail': 'http://www.tagesschau.de' + thumbnail,
            'formats': formats,
            'description': self._og_search_description(webpage).strip(),
        }
