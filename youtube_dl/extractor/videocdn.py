# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..compat import (
    compat_str,
    compat_urlparse,
)

from ..utils import determine_ext


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

        formats = []

        video_id = self._search_regex(
            r'(?ims)<div[^>]+mi24-video-player+.*video-id=[\"\'](?P<videoid>[A-Za-z0-9_-]+)',
            webpage, 'video id', group='videoid')

        thumbnail = self._search_regex(
            r'\"thumbnailUrl\":\"(?P<thumbnail>[^\"]+)',
            webpage, 'thumbnail', group='thumbnail')

        title = self._search_regex(
            r'\"name\":\"(?P<title>[^\"]+)',
            webpage, 'title', group='title')

        manifest_url = self._search_regex(
            r'\"contentUrl\":\"(?P<manifesturl>[^\"]+)',
            webpage,
            'manifest_url', group='manifesturl'
        )

        if isinstance(manifest_url, compat_str) and determine_ext(manifest_url) == 'm3u8':
            formats.extend(self._extract_m3u8_formats(
                compat_urlparse.urljoin(url, manifest_url),
                video_id, 'mp4',
                entry_protocol='m3u8_native', m3u8_id='m3u8'))

        return {
            'id': video_id,
            'title': title,
            'thumbnail': thumbnail,
            'formats': formats,
        }
