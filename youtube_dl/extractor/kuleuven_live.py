# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor


class KULLiveIE(InfoExtractor):
    _VALID_URL = r'(?:(?:https?://(?:www\.)?livestream.kuleuven\.be/\?pin=)|kulive:)(?P<id>[0-9]+)'

    def _real_extract(self, url):
        pin = self._match_id(url)

        json_res = self._download_json(
            "https://icts-p-toledo-streaming-video-live-backend.cloud.icts.kuleuven.be/api/viewers/" + pin,
            pin,
            'Requesting stream URL',
            errnote='The stream with pin %s does not exist or has not started yet' % pin,
            fatal=True)

        m3u8_url = json_res['streamUrl']

        formats = self._extract_m3u8_formats(m3u8_url, pin, 'mp4')

        return {
            'id': pin,
            'title': 'kul-stream',
            'is_live': True,
            'formats': formats,
        }
