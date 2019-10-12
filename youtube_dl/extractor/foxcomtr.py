# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor


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
        {
            'url': 'https://www.foxplay.com.tr/4N1K-2/izle',
            'md5': '74fb90d11d519c194e31b77e966bb252',
            'info_dict': {
                'id': 'izle',
                'ext': 'ts',
                'title': '4N1K 2 FOXPlay\'de | Ücretsiz HD Kalitede Film İzle',
            }
        },
        {
            'url': 'https://www.foxplay.com.tr/Mucize-Doktor/bolumler/4-bolum',
            'md5': '38a8f999e236758f00e7f487560a59ad',
            'info_dict': {
                'id': '4-bolum',
                'ext': 'ts',
                'title': 'Mucize Doktor Dizisi 4. Bölümü İzle',
            }
        },
    ]

    def _real_extract(self, url):
        video_id = self._generic_id(url)

        webpage = self._download_webpage(url, video_id)

        title = self._og_search_title(webpage, default=None).strip()

        m3u8_url = self._html_search_regex(r"videoSrc : '(.*)'",
                                           webpage, 'root_url')
        return {
            'id': video_id,
            'title': title,
            'formats': reversed(self._extract_m3u8_formats(
                m3u8_url, video_id, 'ts', 'm3u8_native')),
        }
