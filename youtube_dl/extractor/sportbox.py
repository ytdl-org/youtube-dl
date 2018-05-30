# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    determine_ext,
    int_or_none,
    js_to_json,
)


class SportBoxEmbedIE(InfoExtractor):
    _VALID_URL = r'https?://news\.sportbox\.ru/vdl/player(?:/[^/]+/|\?.*?\bn?id=)(?P<id>\d+)'
    _TESTS = [{
        'url': 'http://news.sportbox.ru/vdl/player/ci/211355',
        'info_dict': {
            'id': '211355',
            'ext': 'mp4',
            'title': '211355',
            'thumbnail': r're:^https?://.*\.jpg$',
            'duration': 292,
            'view_count': int,
        },
        'params': {
            # m3u8 download
            'skip_download': True,
        },
    }, {
        'url': 'http://news.sportbox.ru/vdl/player?nid=370908&only_player=1&autostart=false&playeri=2&height=340&width=580',
        'only_matching': True,
    }, {
        'url': 'https://news.sportbox.ru/vdl/player/media/193095',
        'only_matching': True,
    }]

    @staticmethod
    def _extract_urls(webpage):
        return re.findall(
            r'<iframe[^>]+src="(https?://news\.sportbox\.ru/vdl/player[^"]+)"',
            webpage)

    def _real_extract(self, url):
        video_id = self._match_id(url)

        webpage = self._download_webpage(url, video_id)

        wjplayer_data = self._parse_json(
            self._search_regex(
                r'(?s)wjplayer\(({.+?})\);', webpage, 'wjplayer settings'),
            video_id, transform_source=js_to_json)

        formats = []
        for source in wjplayer_data['sources']:
            src = source.get('src')
            if not src:
                continue
            if determine_ext(src) == 'm3u8':
                formats.extend(self._extract_m3u8_formats(
                    src, video_id, 'mp4', entry_protocol='m3u8_native',
                    m3u8_id='hls', fatal=False))
            else:
                formats.append({
                    'url': src,
                })
        self._sort_formats(formats)

        view_count = int_or_none(self._search_regex(
            r'Просмотров\s*:\s*(\d+)', webpage, 'view count', default=None))

        return {
            'id': video_id,
            'title': video_id,
            'thumbnail': wjplayer_data.get('poster'),
            'duration': int_or_none(wjplayer_data.get('duration')),
            'view_count': view_count,
            'formats': formats,
        }
