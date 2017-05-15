# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import js_to_json


class SportBoxEmbedIE(InfoExtractor):
    _VALID_URL = r'https?://news\.sportbox\.ru/vdl/player(?:/[^/]+/|\?.*?\bn?id=)(?P<id>\d+)'
    _TESTS = [{
        'url': 'http://news.sportbox.ru/vdl/player/ci/211355',
        'info_dict': {
            'id': '211355',
            'ext': 'mp4',
            'title': 'В Новороссийске прошел детский турнир «Поле славы боевой»',
            'thumbnail': r're:^https?://.*\.jpg$',
        },
        'params': {
            # m3u8 download
            'skip_download': True,
        },
    }, {
        'url': 'http://news.sportbox.ru/vdl/player?nid=370908&only_player=1&autostart=false&playeri=2&height=340&width=580',
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

        formats = []

        def cleanup_js(code):
            # desktop_advert_config contains complex Javascripts and we don't need it
            return js_to_json(re.sub(r'desktop_advert_config.*', '', code))

        jwplayer_data = self._parse_json(self._search_regex(
            r'(?s)player\.setup\(({.+?})\);', webpage, 'jwplayer settings'), video_id,
            transform_source=cleanup_js)

        hls_url = jwplayer_data.get('hls_url')
        if hls_url:
            formats.extend(self._extract_m3u8_formats(
                hls_url, video_id, ext='mp4', m3u8_id='hls'))

        rtsp_url = jwplayer_data.get('rtsp_url')
        if rtsp_url:
            formats.append({
                'url': rtsp_url,
                'format_id': 'rtsp',
            })

        self._sort_formats(formats)

        title = jwplayer_data['node_title']
        thumbnail = jwplayer_data.get('image_url')

        return {
            'id': video_id,
            'title': title,
            'thumbnail': thumbnail,
            'formats': formats,
        }
