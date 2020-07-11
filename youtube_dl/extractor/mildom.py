# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..compat import compat_str
from ..utils import try_get


class MildomIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?mildom\.com/playback/(?P<channel>[0-9]+)\?v_id=(?P<id>[-0-9]+)'
    _VIDEO_INFO_BASE_URL = 'https://cloudac.mildom.com/nonolive/videocontent/playback/getPlaybackDetail'
    _TEST = {
        'url': 'https://www.mildom.com/playback/10819667?v_id=10819667-1594032863',
        'md5': 'bed067a7dff3492184bd06d6131dd8be',
        'info_dict': {
            'id': '10819667-1594032863',
            'ext': 'mp4',
            'title': '月曜!雀荘ほめちぎり　#1',
            'thumbnail': r're:^https?://.*\.png$',
            'description': '#1 記念すべき初回の出演者は声優の高木美佑さんとVtuber界の麻雀つよつよ先生こと千羽黒乃さん！\nMildom公式番組『麻雀番組』毎週月曜に生放送！\n麻雀アプリも使った視聴者対戦型麻雀バラエティ！',
            'uploader': '月曜！雀荘ほめちぎり'
        }
    }

    def _real_extract(self, url):
        channel_id, video_id = re.match(self._VALID_URL, url).groups()

        webpage = self._download_webpage(url, video_id)
        video_data = self._download_json(
            self._VIDEO_INFO_BASE_URL + '?v_id=%s' % video_id, video_id)
        playback_data = video_data['body']['playback']

        video_url = playback_data['source_url']
        description = playback_data.get('video_intro')
        uploader = try_get(playback_data, lambda x: x['author_info']['login_name'], compat_str)
        title = playback_data.get('title')
        if not title:
            title = self._html_search_meta(
                ['og:description', 'description'],
                webpage, 'title', default=None)
        thumbnail = playback_data.get('video_pic')
        if not thumbnail:
            thumbnail = self._html_search_meta(
            'og:image',
            webpage, 'thumbnail', default=None)

        return {
            'id': video_id,
            'title': title,
            'url': video_url,
            'uploader': uploader,
            'channel_id': channel_id,
            'thumbnail': thumbnail,
            'description': description
        }
