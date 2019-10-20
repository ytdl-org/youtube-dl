# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import int_or_none


class TelemadridIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?telemadrid\.es/[^/]+/[^/]+/(?P<display_id>.+?)--\d+.html'
    _TESTS = [
        {
            'url': 'http://www.telemadrid.es/programas/telenoticias-fin-de-semana/cerca-lejos-nuevo-Klapisch-2-2169403070--20191020083747.html',
            'info_dict': {
                'id': '6096258464001',
                'ext': 'mp4',
                'title': '&#039;Tan cerca, tan lejos&#039;, lo nuevo de Klapisch',
                'description': 'md5:10ac0514bdbdeeea9de495ae0720c6ff',
                'thumbnail': r're:^https?://images.telemadrid.es/2019/10/20/programas/telenoticias-fin-de-semana/cerca-lejos-nuevo-Klapisch_2169403070_7342970_1300x813.png$',
                'timestamp': 1571596692,
                'upload_date': '20191020'
            }
        },
        {
            'url': 'http://www.telemadrid.es/programas/telenoticias-fin-de-semana/Doce-detenidos-altercados-registrados-Madrid-2-2169403042--20191020100828.html',
            'info_dict': {
                'id': '6096226698001',
                'ext': 'mp4',
                'title': 'Doce detenidos en los altercados registrados en el centro de Madrid',
                'description': 'md5:77a37a10cfe8b8cd595d11bf762e90da',
                'thumbnail': r're:^https?://images.telemadrid.es/2019/10/20/programas/telenoticias-fin-de-semana/Doce-detenidos-altercados-registrados-Madrid_2169403042_7342376_4000x2666.jpg$',
                'timestamp': 1571573534,
                'upload_date': '20191020'
            }
        },
        {
            'url': 'http://www.telemadrid.es/programas/120-minutos/minutos-Parte-uno-2-2165803426--20191008033109.html',
            'info_dict': {
                'id': '6093135605001',
                'ext': 'mp4',
                'title': '120 minutos 08.10.2019 (Parte 1)',
                'description': 'md5:eea20844c4aef07638b53d8f40fe8e23',
                'thumbnail': r're:^https?://images.telemadrid.es/2019/10/08/programas/120-minutos/minutos-Parte-uno_2165803426_7312298_1920x1080.jpg$',
                'timestamp': 1570541701,
                'upload_date': '20191008'
            }
        }
    ]

    _VIDEO_BASE = 'http://c.brightcove.com/services/mobile/streaming/index/master.m3u8?videoId='

    def _real_extract(self, url):
        display_id = re.match(self._VALID_URL, url).groups()
        webpage = self._download_webpage(url, display_id)

        video_figure = self._search_regex(r'<figure[^>]+class=\"media-video\"[^>]+itemtype=\"http://schema\.org/VideoObject\"*>(.*?)</figure>', webpage, 'video_figure', flags=re.DOTALL)
        video_id = self._search_regex(r'<video.+data-video-id=\"(.+?)\".+</video>', video_figure, 'video_id', flags=re.DOTALL)
        name = self._search_regex(r'<meta itemprop=\"name\" content=\"(.*?)\">', video_figure, 'name', flags=re.DOTALL)
        description = self._html_search_regex(r'<meta itemprop=\"description\" content=\"(.*?)\">', video_figure, 'description', flags=re.DOTALL)
        thumbnail = self._search_regex(r'<meta itemprop=\"thumbnailUrl\" content=\"(.*?)\">', video_figure, 'thumbnail', flags=re.DOTALL)
        timestamp = self._search_regex(r'<meta itemprop=\"uploadDate\" content=\"(.*?)\">', video_figure, 'timestamp', flags=re.DOTALL)

        formats = self._extract_m3u8_formats(self._VIDEO_BASE + video_id, video_id, 'mp4', 'm3u8_native', m3u8_id='hls', fatal=False)

        return {
            'id': video_id,
            'display_id': display_id,
            'title': name,
            'description': description,
            'thumbnail': thumbnail,
            'timestamp': int_or_none(timestamp),
            'formats': formats
        }
