# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor


class SkylineWebcamsIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?skylinewebcams\.com/[^/]+/webcam/(?:[^/]+/)+(?P<id>[^/]+)\.html'
    _TEST = {
        'url': 'https://www.skylinewebcams.com/it/webcam/italia/lazio/roma/scalinata-piazza-di-spagna-barcaccia.html',
        'info_dict': {
            'id': 'piazza-di-spagna',
            'ext': 'mp4',
            'title': 're:^【LIVE】 Webcam Roma - Piazza di Spagna | SkylineWebcams [0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}$',
            'description': 'Guarda la webcam su Piazza di Spagna a Roma! Scopri in diretta il traffico dei turisti ai piedi della scalinata di Trinità dei Monti ed intorno alla Barcaccia',
            'is_live': True,
        },
        'params': {
            'skip_download': True,
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)

        webpage = self._download_webpage(url, video_id)
        stream_url = 'https://hd-auth.skylinewebcams.com/live.m3u8' + self._search_regex(
            r'(?:url|source)\s*:\s*(["\'])(livee\.m3u8(?P<a_param>\?a=\w+))\1', webpage,
            'stream url', group='a_param')

        title = self._og_search_title(webpage)
        description = self._og_search_description(webpage)

        return {
            'id': video_id,
            'url': stream_url,
            'ext': 'mp4',
            'title': self._live_title(title),
            'description': description,
            'is_live': True,
        }
