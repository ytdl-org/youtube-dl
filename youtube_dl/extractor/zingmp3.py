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

    def _extract_item(self, item):
        item_id = item.get('id')
        if not item_id:
            return

        item_title = (item.get('name') or item.get('title')).strip()
        if len(item_title) < 1:
            return

        item_type = item.get('type')
        if not item_type:
            return

        formats = []
        for quality, source_url in item.get('source', []).items():
            if not source_url:
                continue
            source_url = self._proto_relative_url(source_url, 'http:')
            quality_num = int_or_none(quality)
            f = {
                'format_id': quality,
                'url': source_url,
            }
            if item_type == 'video':
                f.update({
                    'height': quality_num,
                    'ext': 'mp4',
                })
            elif item_type == 'audio':
                f.update({
                    'abr': quality_num,
                    'ext': 'mp3',
                })
            else:
                continue
            formats.append(f)

        if len(formats) < 1:
            return

        thumbnail = item.get('thumbnail')

        return {
            'id': item_id,
            'title': item_title,
            'formats': formats,
            'thumbnail': thumbnail if thumbnail else None,
            'artist': item.get('artist'),
        }

    def _extract_player_json(self, url, player_json_url, id, title=None):
        player_json = self._download_json(
            player_json_url, id, 'Downloading Player JSON',
            headers={'Referer': url})

        items = [player_json['data']]
        if 'items' in items[0]:
            items = items[0]['items']

        if len(items) == 1:
            # audio/video
            return self._extract_item(items[0])
        else:
            # album/playlist
            entries = []

            for i, item in enumerate(items, 1):
                entry = self._extract_item(item)
                if not entry:
                    continue
                entries.append(entry)

            return {
                '_type': 'playlist',
                'id': id,
                'title': title,
                'entries': entries,
            }


class ZingMp3IE(ZingMp3BaseInfoExtractor):
    _VALID_URL = r'https?://mp3\.zing\.vn/(?:bai-hat|album|playlist|video-clip)/[^/]+/(?P<id>\w+)\.html'
    _TESTS = [{
        'url': 'http://mp3.zing.vn/bai-hat/Xa-Mai-Xa-Bao-Thy/ZWZB9WAB.html',
        'md5': 'ead7ae13693b3205cbc89536a077daed',
        'info_dict': {
            'id': 'ZWZB9WAB',
            'title': 'Xa Mãi Xa',
            'ext': 'mp3',
            'thumbnail': r're:^https?://.*\.jpg$',
        },
    }, {
        'url': 'http://mp3.zing.vn/video-clip/Let-It-Go-Frozen-OST-Sungha-Jung/ZW6BAEA0.html',
        'md5': 'c04f2c8c6400d90b43dd0fa6485e2e32',
        'info_dict': {
            'id': 'ZW6BAEA0',
            'title': 'Let It Go (Frozen OST)',
            'ext': 'mp4',
        },
    }, {
        'url': 'http://mp3.zing.vn/album/Lau-Dai-Tinh-Ai-Bang-Kieu-Minh-Tuyet/ZWZBWDAF.html',
        'info_dict': {
            '_type': 'playlist',
            'id': 'ZWZBWDAF',
            'title': 'Lâu Đài Tình Ái  - Bằng Kiều | Zing MP3',
        },
        'playlist_count': 10,
    }, {
        'url': 'http://mp3.zing.vn/playlist/Sofm-s-playlist-louissofm/IWE606EA.html',
        'info_dict': {
            '_type': 'playlist',
            'id': 'IWE606EA',
            'title': 'Sofm\'s playlist  -  | Zing MP3',
        },
        'playlist_count': 98,
    }]
    IE_NAME = 'zingmp3'
    IE_DESC = 'mp3.zing.vn'

    def _real_extract(self, url):
        page_id = self._match_id(url)

        webpage = self._download_webpage(url, page_id)

        player_url = self._search_regex([
            r'data-xml="([^"]+)',
            r'&amp;xmlURL=([^&]+)&',
            r'xmlurl: \'([^\']+)\''
        ], webpage, 'player url')

        title = self._og_search_title(webpage)
        player_url_full = 'https://mp3.zing.vn/xhr' + player_url

        return self._extract_player_json(url, player_url_full, page_id, title)
