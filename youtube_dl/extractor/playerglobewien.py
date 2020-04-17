# coding: utf-8
from __future__ import unicode_literals

import re
from .common import InfoExtractor


class PlayerGlobeWienIE(InfoExtractor):
    _VALID_URL = r'https?://player\.(hader\.at|globe\.wien)/[^/]+/(?P<id>[^/?#]+)'
    _TESTS = [
        {
            'url': 'https://player.globe.wien/globe-wien/corona-podcast-teil-4',
            'md5': 'f973a27e258bdeff686e63434e872f70',
            'info_dict': {
                'id': 'corona-podcast-teil-4',
                'ext': 'mp4',
                'title': 'Eckel & Niavarani & Sarsam - Im Endspurt versagt',
                'description': 'md5:fbd2e2a456fef3a171683dd9e33f1810',
                'thumbnail': r're:^https?://.*\.jpg',
            },
            'params': {
                'format': 'bestvideo',
                'skip_download': True,
            }
        },
        {
            'url': 'https://player.hader.at/hader/hader-indien-video',
            'md5': '0bca8d5b309361a9556cee6abff2c1b9',
            'info_dict': {
                'id': 'hader-indien-video',
                'ext': 'mp4',
                'title': 'Film der Woche - Indien',
                'description': 'md5:cad9f2bd7a0c5c0dff9cf1cff71288f6',
                'thumbnail': r're:^https?://.*\.jpg',
            },
            'params': {
                'format': 'bestvideo',
                'skip_download': True,
            }
        },
        {
            'url': 'https://player.hader.at/hader/hader-indien',
            'md5': 'b8bd7cf37d82529411a6e67005739fb3',
            'info_dict': {
                'id': 'hader-indien',
                'ext': 'mp3',
                'title': 'Hader & Dorfer lesen Indien',
                'description': 'md5:8b4e1de6c627b7d9ee6cb1c65debfa85',
                'thumbnail': r're:^https?://.*\.jpg',
            },
            'params': {
                'skip_download': True,
            }
        },
    ]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)
        next_data = self._parse_json(
            self._search_regex(
                r'<script[^>]+id="__NEXT_DATA__"[^>]+type="application/json"[^>]*>([^<]+)</script>',
                webpage, 'next data'),
            video_id)

        vod = next_data.get('props').get('initialState').get('vod')

        formats = []
        for key in vod.get('streamUrl'):
            src_url = vod.get('streamUrl').get(key)
            if key == 'hls':
                formats.extend(self._extract_m3u8_formats(
                    src_url, video_id, ext='mp4', m3u8_id=key, fatal=False))
            elif key == 'dash':
                formats.extend(self._extract_mpd_formats(
                    src_url, video_id, mpd_id=key, fatal=False))
            else:
                formats.append({
                    'format_id': key,
                    'url': src_url
                })

        thumbnails = []
        for key in vod.get('images'):
            thumbnails.append({
                'id': key,
                'url': vod.get('images').get(key),
            })
        self._check_formats(formats, video_id)
        self._sort_formats(formats)

        return {
            'id': vod.get('id'),
            'title': vod.get('title'),
            'description': vod.get('teaserDescription'),
            'release_year': vod.get('year'),
            'duration': (vod.get('durationMinutes') or 0) * 60,
            'formats': formats,
            'thumbnails': thumbnails,
        }
