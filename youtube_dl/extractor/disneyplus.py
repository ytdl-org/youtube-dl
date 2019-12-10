# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import int_or_none


class DisneyPlusIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?disneyplus\.com/[^/]+/[^/]+/(?P<display_id>.+?)--\d+.html'
    _TEST = {
    }
    _VIDEO_BASE = 'http://disneyplus.com/services/mobile/streaming/index/master.m3u8?videoId='

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
