# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor


class KULLiveIE(InfoExtractor):
    _VALID_URL = r'(?:(?:https?://(?:www\.)?livestream.kuleuven\.be/\?pin=)|kulive:)(?P<id>[0-9]+)'
    BACKEND_BASE_URL = "https://icts-p-toledo-streaming-video-live-backend.cloud.icts.kuleuven.be/api/viewers/"

    def _real_extract(self, url):
        pin = self._match_id(url)

        json_res = self._download_json(self.BACKEND_BASE_URL + pin, pin, 'Requesting stream URL')
        m3u8_url = json_res['streamUrl']

        formats = self._extract_m3u8_formats(m3u8_url, pin, 'mp4')

        return {
            'id': pin,
            'title': 'kul-stream',
            'is_live': True,
            'formats': formats,
        }
