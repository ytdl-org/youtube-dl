# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor


class SkylineWebcamsIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?skylinewebcams\.com/[^/]+/webcam/(?:[^/]+/)+(?P<id>[^/]+)\.html'
    _TEST = {
        'url': 'https://www.skylinewebcams.com/it/webcam/italia/lazio/roma/scalinata-piazza-di-spagna-barcaccia.html',
        'info_dict': {
            'id': 'scalinata-piazza-di-spagna-barcaccia',
            'ext': 'mp4',
            'title': 're:^Live Webcam Scalinata di Piazza di Spagna - La Barcaccia [0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}$',
            'description': 'Roma, veduta sulla Scalinata di Piazza di Spagna e sulla Barcaccia',
            'is_live': True,
        },
        'params': {
            'skip_download': True,
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)

        webpage = self._download_webpage(url, video_id)

        stream_url = self._search_regex(
            r'(?:url|source)\s*:\s*(["\'])(?P<url>(?:https?:)?(?://)?\S+?\.m3u8.*?)\1', webpage,
            'stream url', group='url')

        if 'skylinewebcams.com' not in stream_url and 'livee.m3u8' in stream_url:
            stream_url = stream_url.replace('livee.m3u8', 'https://hd-auth.skylinewebcams.com/live.m3u8')

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
