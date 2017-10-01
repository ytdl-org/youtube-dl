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

        for quality, source_url in item['source'].items():
            if not source_url or source_url == 'require vip':
                continue
            if not re.match(r'https?://', source_url):
                source_url = '//' + source_url
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

        #cover = item.get('cover')

        return {
            'title': (item.get('name') or item.get('title')).strip(),
            'formats': formats,
            #'thumbnail': 'http:/' + cover if cover else None,
            'artist': item.get('artist'),
        }

    def _extract_player_json(self, player_json_url, id, page_type, playlist_title=None):
        player_json = self._download_json(player_json_url, id, 'Downloading Player JSON')

        items = player_json['data']
        if 'items' in items:
            items = items['items']

        if page_type == 'audio' or page_type == 'video':
            # one single song
            data = self._extract_item(items, page_type)
            data['id'] = id

            return data
        else:
            # playlist of songs
            entries = []

            for i, item in enumerate(items, 1):
                entry = self._extract_item(item, page_type, fatal=False)
                if not entry:
                    continue
                entry['id'] = '%s-%d' % (id, i)
                entries.append(entry)

            return {
                '_type': 'playlist',
                'id': id,
                'title': playlist_title,
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
        'url': 'http://mp3.zing.vn/album/I-Lab-You-Single-Tien-Tien/ZO6976C0.html',
        'info_dict': {
            '_type': 'playlist',
            'id': 'ZO6976C0',
            'title': 'I Lab You (Single)  - Tiên Tiên | Zing MP3',
        },
        'playlist_count': 2,
    }, {
        'url': 'http://mp3.zing.vn/playlist/Duong-Hong-Loan-apollobee/IWCAACCB.html',
        'only_matching': True,
    }]
    IE_NAME = 'zingmp3'
    IE_DESC = 'mp3.zing.vn'

    def _real_extract(self, url):
        page_id = self._match_id(url)

        webpage = self._download_webpage(url, page_id)

        player_json_url = 'http://mp3.zing.vn/xhr' + self._search_regex([
            r'data-xml="([^"]+)',
            r'&amp;xmlURL=([^&]+)&'
        ], webpage, 'player xml url')

        playlist_title = self._og_search_title(webpage)
        page_type = self._search_regex(r'type=([^&]+)', player_json_url, 'page type', fatal=False, default='audio')

        return self._extract_player_json(player_json_url, page_id, page_type, playlist_title)
