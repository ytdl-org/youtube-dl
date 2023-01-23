# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor

from ..utils import (
    determine_ext,
    urljoin,
)


class VideoCdnIE(InfoExtractor):
    _VALID_URL = r'https?://e\.video-cdn\.net/video?.*video-id=(?P<id>[a-zA-Z0-9-_]+).*'
    _TESTS = [
        {
            'url': 'https://e.video-cdn.net/video?video-id=8eBUrWaMJFS38A5X-j2CgY&player-id=53Tun3ZZpZpVuvaTvsm3jU',
            'info_dict': {
                'id': '8eBUrWaMJFS38A5X-j2CgY',
                'ext': 'mp4',
                'title': 'RiskBuster FireFighter VI - Adventskranz',
                'thumbnail': r're:(?i)https://.*\.jpeg',
            },
        },
        {
            'url': 'https://e.video-cdn.net/video?video-id=91imQ_wKjkTFghe-3mmBAA&player-id=7nCLZ_ESM8rT9YUw6qUGA9',
            'info_dict': {
                'id': '91imQ_wKjkTFghe-3mmBAA',
                'ext': 'mp4',
                'title': 'SCC2019_Talk_Tychsen_TXL.mp4',
                'thumbnail': r're:(?i)https://.*\.jpeg',
            },
        },
    ]

    def _real_extract(self, url):
        video_id = self._match_id(url)

        webpage = self._download_webpage(url, video_id)

        thumbnail = self._search_regex(
            r'\"thumbnailUrl\":\"(?P<thumbnail>[^\"]+)',
            webpage, 'thumbnail', group='thumbnail',
            default=None)

        title = self._search_regex(r'"name"\s*:\s*"((?:\\"|[^"])+)', webpage, 'title')

        manifest_url = self._search_regex(r'"contentUrl"\s*:\s*"((?:\\"|[^"])+)', webpage, 'manifest_url')
        manifest_url = urljoin(url, manifest_url)

        formats = []
        if manifest_url and determine_ext(manifest_url) == 'm3u8':
            formats.extend(self._extract_m3u8_formats(
                manifest_url, video_id, 'mp4',
                entry_protocol='m3u8_native', m3u8_id='m3u8'))
            self._sort_formats(formats)

        return {
            'id': video_id,
            'title': title,
            'thumbnail': thumbnail,
            'formats': formats,
        }
