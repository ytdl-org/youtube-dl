# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import int_or_none


class TelemadridIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?telemadrid\.es/[^/]+/[^/]+/(?P<display_id>.+?)--\d+.html'
    _TEST = {
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
