# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor


class PlayerGlobeWienIE(InfoExtractor):
    _VALID_URL = r'https?://player.globe.wien/globe-wien/(?P<id>.*)'
    _TESTS = [{
        'url': 'https://player.globe.wien/globe-wien/corona-podcast-teil-4',
        'info_dict': {
            'id': 'corona-podcast-teil-4',
            'ext': 'mp4',
            'title': 'Globe Wien VOD - Eckel & Niavarani & Sarsam - Im Endspurt versagt',
        },
        'params': {
            'format': 'bestvideo',
        }
    }, {
        'url': 'https://player.globe.wien/globe-wien/corona-podcast-teil-4',
        'info_dict': {
            'id': 'corona-podcast-teil-4',
            'ext': 'mp4',
            'title': 'Globe Wien VOD - Eckel & Niavarani & Sarsam - Im Endspurt versagt',
        },
        'params': {
            'format': 'bestaudio',
        }
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        print(video_id)
        webpage = self._download_webpage(url, video_id)
        formats = []
        title = self._html_search_regex(r'<title>(.+?)</title>', webpage, 'title')

        stream_url = self._download_webpage("https://player.globe.wien/api/playout?vodId=" + video_id, video_id)

        hls_url = self._parse_json(stream_url, video_id)['streamUrl']['hls']

        formats.extend(self._extract_m3u8_formats(
            hls_url, video_id, 'mp4', entry_protocol='m3u8_native', m3u8_id='hls'))

        self._sort_formats(formats)
        return {
            'id': video_id,
            'title': title,
            'formats': formats,
        }
