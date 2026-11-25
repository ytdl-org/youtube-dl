# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import (
    try_get,
    unified_timestamp,
)


class HololiveFCIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?hololive-fc\.com/video/(?P<id>[a-zA-Z0-9]+)'
    _TEST = {
        'url': 'https://hololive-fc.com/video/smikfVmVrbNwJpiZ6KNzHHNT',
        'md5': 'e4c26ea3bc17557873cc7bbc72de2165',
        'info_dict': {
            'id': 'smikfVmVrbNwJpiZ6KNzHHNT',
            'ext': 'mp4',
            'title': '【ホロライブ・サマー2022】これが本当のホロライブサマー！？ #1',
            'thumbnail': r're:^https?://',
            'description': 'md5:24f1c21b051de003cd81ed6ed11278ce',
            'release_timestamp': 1660042200,
            'view_count': int,
            'comment_count': int,
            'tags': ['ロボ子さん', 'アキ・ローゼンタール', '赤井はあと', '癒月ちょこ', '宝鐘マリン', '白銀ノエル', '尾丸ポルカ', 'ラプラス・ダークネス'],
        }
    }
    _API_BASE_URL = 'https://nfc-api.hololive-fc.com/fc/video_pages/'

    def _real_extract(self, url):
        video_id = self._match_id(url)

        video_info_url = self._API_BASE_URL + video_id
        video_info = self._download_json(video_info_url, video_id)['data']['video_page']

        session_id_url = self._API_BASE_URL + video_id + '/session_ids'
        session_id = self._download_json(session_id_url, video_id, data={})['data']['session_id']

        m3u8_url = video_info['video_stream']['authenticated_url'].format(session_id=session_id)
        formats = self._extract_m3u8_formats(m3u8_url, video_id, 'mp4')
        self._sort_formats(formats)

        return {
            'id': video_id,
            'title': video_info['title'],
            'formats': formats,
            'thumbnail': video_info.get('thumbnail_url'),
            'description': video_info.get('description'),
            'release_timestamp': unified_timestamp(video_info.get('released_at')),
            'view_count': try_get(video_info, lambda x: x['video_aggregate_info']['total_views'], int),
            'comment_count': try_get(video_info, lambda x: x['video_aggregate_info']['number_of_comments'], int),
            'tags': try_get(video_info, lambda x: [tag['tag'] for tag in x['video_tags']], list),
        }
