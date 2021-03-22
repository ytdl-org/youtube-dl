# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor


class ZingMp3BaseInfoExtractor(InfoExtractor):

    def _v2_extract_id(self, url):
        return re.search(r'([A-Z0-9]+)\.html', url).group(1)

    def _v2_extract_track(self, data):
        itemId = self._v2_extract_id(data.get('url'))
        track_data = data.get('item') or data

        formats = []
        artist = None
        if track_data.get('@type') == 'MusicRecording':
            artist = track_data.get('byArtist')[0].get('name') if track_data.get('byArtist') else None
            formats = [
                {
                    'format_id': '128',
                    'url': 'http://api.mp3.zing.vn/api/streaming/audio/' + itemId + '/128',
                    'ext': 'mp3',
                    'abr': 128
                },
                {
                    'format_id': '320',
                    'url': 'http://api.mp3.zing.vn/api/streaming/audio/' + itemId + '/320',
                    'ext': 'mp3',
                    'abr': 320
                }
            ]
        elif track_data.get('@type') == 'Movie':
            artist = track_data.get('producer').get('name') if track_data.get('producer') else None
            formats = [
                {
                    'format_id': '360p',
                    'url': 'http://api.mp3.zing.vn/api/streaming/video/' + itemId + '/360',
                    'ext': 'mp4',
                    'height': 360
                },
                {
                    'format_id': '480p',
                    'url': 'http://api.mp3.zing.vn/api/streaming/video/' + itemId + '/480',
                    'ext': 'mp4',
                    'height': 480
                },
                {
                    'format_id': '720p',
                    'url': 'http://api.mp3.zing.vn/api/streaming/video/' + itemId + '/720',
                    'ext': 'mp4',
                    'height': 720
                },
                {
                    'format_id': '1080p',
                    'url': 'http://api.mp3.zing.vn/api/streaming/video/' + itemId + '/1080',
                    'ext': 'mp4',
                    'height': 1080
                }
            ]

        track = {
            'id': itemId,
            'title': track_data.get('name'),
            'formats': formats,
            'thumbnail': track_data.get('image'),
            'artist': artist
        }
        return track


class ZingMp3IE(ZingMp3BaseInfoExtractor):
    _VALID_URL = r'https?://(mp3\.zing\.vn|zingmp3\.vn)/(?:bai-hat|album|playlist|video-clip)/[^/]+/(?P<id>\w+)\.html'
    _TESTS = [{
        'url': 'http://zingmp3.vn/bai-hat/Xa-Mai-Xa-Bao-Thy/ZWZB9WAB.html',
        'md5': 'ead7ae13693b3205cbc89536a077daed',
        'info_dict': {
            'id': 'ZWZB9WAB',
            'title': 'Xa Mãi Xa',
            'ext': 'mp3',
            'thumbnail': r're:^https?://.*\.jpg$',
        },
    }, {
        'url': 'http://zingmp3.vn/video-clip/Let-It-Go-Frozen-OST-Sungha-Jung/ZW6BAEA0.html',
        'md5': '870295a9cd8045c0e15663565902618d',
        'info_dict': {
            'id': 'ZW6BAEA0',
            'title': 'Let It Go (Frozen OST)',
            'ext': 'mp4',
        },
    }, {
        'url': 'http://zingmp3.vn/album/Lau-Dai-Tinh-Ai-Bang-Kieu-Minh-Tuyet/ZWZBWDAF.html',
        'info_dict': {
            '_type': 'playlist',
            'id': 'ZWZBWDAF',
            'title': 'Lâu Đài Tình Ái - Bằng Kiều,Minh Tuyết | Album 320 lossless',
        },
        'playlist_count': 10,
        'skip': 'removed at the request of the owner',
    }, {
        'url': 'http://mp3.zing.vn/playlist/Duong-Hong-Loan-apollobee/IWCAACCB.html',
        'only_matching': True,
    }]
    IE_NAME = 'zingmp3'
    IE_DESC = 'mp3.zing.vn,zingmp3.vn'

    def _real_extract(self, url):
        page_id = self._match_id(url)

        webpage = self._download_webpage(url, page_id)

        # extract ld+json schema.org
        matchjson = re.search(r'<script type="application/ld\+json">((?:\n|\r\n?|[^<])+)</script>$', webpage, re.MULTILINE)

        if matchjson:
            data = self._parse_json(matchjson.group(1), page_id)

            if data.get('@type') == 'MusicPlaylist':
                entries = []
                for track_data in data.get('track').get('itemListElement'):
                    entries.append(self._v2_extract_track(track_data))
                playlist = {
                    '_type': 'playlist',
                    'id': self._v2_extract_id(data.get('url')),
                    'title': data.get('title'),
                    'entries': entries,
                }
                return playlist
            else:
                track = self._v2_extract_track(data)
                return track

        return
