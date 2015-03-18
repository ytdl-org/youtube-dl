# coding: utf-8
from __future__ import unicode_literals

import random
import time

from .common import InfoExtractor
from ..utils import strip_jsonp


class QQMusicIE(InfoExtractor):
    _VALID_URL = r'http://y.qq.com/#type=song&mid=(?P<id>[0-9A-Za-z]+)'
    _TESTS = [{
        'url': 'http://y.qq.com/#type=song&mid=004295Et37taLD',
        'md5': 'bed90b6db2a7a7a7e11bc585f471f63a',
        'info_dict': {
            'id': '004295Et37taLD',
            'ext': 'm4a',
            'title': '可惜没如果',
            'upload_date': '20141227',
            'creator': '林俊杰',
        }
    }]

    # Reference: m_r_GetRUin() in top_player.js
    # http://imgcache.gtimg.cn/music/portal_v3/y/top_player.js
    @staticmethod
    def m_r_get_ruin():
        curMs = int(time.time() * 1000) % 1000
        return int(round(random.random() * 2147483647) * curMs % 1E10)

    def _real_extract(self, url):
        mid = self._match_id(url)

        detail_info_page = self._download_webpage(
            'http://s.plcloud.music.qq.com/fcgi-bin/fcg_yqq_song_detail_info.fcg?songmid=%s&play=0' % mid,
            mid, note='Download sont detail info',
            errnote='Unable to get song detail info')

        song_name = self._html_search_regex(
            r"songname:\s*'([^']+)'", detail_info_page, 'song name')

        publish_time = self._html_search_regex(
            r'发行时间：(\d{4}-\d{2}-\d{2})', detail_info_page,
            'publish time').replace('-', '')

        singer = self._html_search_regex(
            r"singer:\s*'([^']+)", detail_info_page, 'singer')

        guid = self.m_r_get_ruin()

        vkey = self._download_json(
            'http://base.music.qq.com/fcgi-bin/fcg_musicexpress.fcg?json=3&guid=%s' % guid,
            mid, note='Retrieve vkey', errnote='Unable to get vkey',
            transform_source=strip_jsonp)['key']
        song_url = 'http://cc.stream.qqmusic.qq.com/C200%s.m4a?vkey=%s&guid=%s&fromtag=0' % (mid, vkey, guid)

        return {
            'id': mid,
            'url': song_url,
            'title': song_name,
            'upload_date': publish_time,
            'creator': singer,
        }
