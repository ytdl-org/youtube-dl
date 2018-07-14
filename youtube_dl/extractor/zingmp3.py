# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    int_or_none,
    update_url_query,
)


class ZingMp3BaseInfoExtractor(InfoExtractor):

    def _extract_item(self, item, page_type, fatal=True):
        error_message = item.get('msg')
        if error_message:
            if not fatal:
                return
            raise ExtractorError(
                '%s returned error: %s' % (self.IE_NAME, error_message),
                expected=True)

        formats = []
        sources = item.get('source', {})
        for (quality, source_url) in sources.items():
            if not source_url or source_url == 'require vip':
                continue

            source_url = self._proto_relative_url(source_url, 'http:')
            quality_num = int_or_none(quality)
            f = {
                'format_id': quality,
                'url': source_url,
            }
            if page_type == 'video':
                f.update({
                    'height': quality_num,
                    'ext': 'mp4',
                })
            else:
                f.update({
                    'abr': quality_num,
                    'ext': 'mp3',
                })
            formats.append(f)

        artist = None
        try:
            artist = item['artist']['name']
        except KeyError:
            pass

        if page_type == 'album':
            return {
                'id': item.get('id'),
                'track_id': item.get('id'),
                'artist': artist,
                'title': (item.get('name') or item.get('title')).strip(),
                'track': (item.get('name') or item.get('title')).strip(),
                'track_number': int_or_none(item.get('order')),
                'formats': formats,
                'thumbnail': item.get('thumbnail'),
            }

        return {
            'id': item.get('id'),
            'artist': artist,
            'title': (item.get('name') or item.get('title')).strip(),
            'formats': formats,
            'thumbnail': item.get('thumbnail'),
        }

    def _extract_player_json(self, player_json_url, id, page_type, playlist_title=None):
        player_json = self._download_json(player_json_url, id, 'Downloading Player JSON')
        if 'items' not in player_json['data']:
            item = player_json['data']
            data = self._extract_item(item, page_type)
            return data

        else:
            # playlist of songs
            entries = []
            for i, item in enumerate(player_json['data']['items'], 1):
                entry = self._extract_item(item, page_type, fatal=False)
                if not entry:
                    continue
                entries.append(entry)

            return {
                '_type': 'playlist',
                'id': id,
                'title': playlist_title,
                'entries': entries,
            }


class ZingMp3IE(ZingMp3BaseInfoExtractor):
    _VALID_URL = r'https?://mp3\.zing\.vn/(?:bai-hat|album|playlist|video-clip)/[^/]+/(?P<id>\w+)\.html'
    _TESTS = [
        {
            'url': 'http://mp3.zing.vn/bai-hat/Xa-Mai-Xa-Bao-Thy/ZWZB9WAB.html',
            'md5': 'ead7ae13693b3205cbc89536a077daed',
            'info_dict': {
                'id': 'ZWZB9WAB',
                'title': 'Xa Mãi Xa',
                'artist': 'Bảo Thy',
                'ext': 'mp3',
                'thumbnail': r're:^https?://.*\.jpg$',
            },
        },
        {
            'url': 'http://mp3.zing.vn/video-clip/Let-It-Go-Frozen-OST-Sungha-Jung/ZW6BAEA0.html',
            'md5': '870295a9cd8045c0e15663565902618d',
            'info_dict': {
                'id': 'ZW6BAEA0',
                'title': 'Let It Go (Frozen OST)',
                'ext': 'mp4',
            },
        },
        {
            'url': 'https://mp3.zing.vn/album/Con-Trong-Ky-Niem-Le-Quyen/ZWZCO9UW.html',
            'info_dict': {
                '_type': 'playlist',
                'id': 'ZWZCO9UW',
                'title': 'Còn Trong Kỷ Niệm  - Lệ Quyên | Zing MP3',
            },
            'playlist_count': 9,
        },
        {
            'url': 'http://mp3.zing.vn/playlist/Duong-Hong-Loan-apollobee/IWCAACCB.html',
            'only_matching': True,
        },
    ]
    IE_NAME = 'zingmp3'
    IE_DESC = 'mp3.zing.vn'

    def _real_extract(self, url):
        page_id = self._match_id(url)

        webpage = self._download_webpage(url, page_id)

        player_json_url = self._search_regex([
            r'data-xml="([^"]+)',
            r'&amp;xmlURL=([^&]+)&'
        ], webpage, 'player xml url')
        player_json_url = "https://mp3.zing.vn/xhr" + player_json_url

        playlist_title = None
        page_type = self._search_regex(r'type=([\w]+)', player_json_url, 'page type')
        if page_type == 'video':
            player_json_url = update_url_query(player_json_url, {'format': 'json'})
        else:
            player_json_url = player_json_url.replace('/xml/', '/html5xml/')
            if page_type == 'album':
                playlist_title = self._og_search_title(webpage)

        return self._extract_player_json(player_json_url, page_id, page_type, playlist_title)
