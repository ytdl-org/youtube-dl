# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import unsmuggle_url


class FoxComTrIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www.)?(?:fox.com.tr/.*|foxplay.com.tr/.*)'
    _TESTS = [
        {
            'url': 'https://www.fox.com.tr/Mucize-Doktor/bolum/1',
            'md5': '4c85845537e99429ca28749340a0c00a',
            'info_dict': {
                'id': '1',
                'ext': 'ts',
                'title': 'FOX | Mucize Doktor 1. Bölüm',
            }
        },
        {
            'url': 'https://www.fox.com.tr/Mucize-Doktor/bolum/2',
            'md5': '04c4f9c72501151ef3ed6a46bd9ecc74',
            'info_dict': {
                'id': '2',
                'ext': 'ts',
                'title': 'FOX | Mucize Doktor 2. Bölüm',
            }
        },
    ]

    def _real_extract(self, url):
        url, smuggled_data = unsmuggle_url(url)
        if smuggled_data and 'force_videoid' in smuggled_data:
            force_videoid = smuggled_data['force_videoid']
            video_id = force_videoid
        else:
            video_id = self._generic_id(url)

        webpage = self._download_webpage(url, video_id)

        title = self._og_search_title(
            webpage, default=None) or self._html_search_regex(
            r'(?s)<title>(.*?)</title>', webpage, 'video title',
            default='video')

        m3u8_url = self._html_search_regex(r"videoSrc : '(.*)'", webpage, 'root_url')
        return {
            'id': video_id,
            'title': title,
            'formats': reversed(self._extract_m3u8_formats(m3u8_url, video_id, 'ts', 'm3u8_native', fatal=False)),
        }
