# coding: utf-8
from __future__ import unicode_literals

import random
import time
import re

from .common import InfoExtractor
from ..utils import (
    strip_jsonp,
    unescapeHTML,
)
from ..compat import compat_urllib_request


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
            'description': 'md5:4348ff1dd24036906baa7b6f973f8d30',
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
            mid, note='Download song detail info',
            errnote='Unable to get song detail info', encoding='gbk')

        song_name = self._html_search_regex(
            r"songname:\s*'([^']+)'", detail_info_page, 'song name')

        publish_time = self._html_search_regex(
            r'发行时间：(\d{4}-\d{2}-\d{2})', detail_info_page,
            'publish time', default=None)
        if publish_time:
            publish_time = publish_time.replace('-', '')

        singer = self._html_search_regex(
            r"singer:\s*'([^']+)", detail_info_page, 'singer', default=None)

        lrc_content = self._html_search_regex(
            r'<div class="content" id="lrc_content"[^<>]*>([^<>]+)</div>',
            detail_info_page, 'LRC lyrics', default=None)

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
            'description': lrc_content,
        }


class QQPlaylistBaseIE(InfoExtractor):
    @staticmethod
    def qq_static_url(category, mid):
        return 'http://y.qq.com/y/static/%s/%s/%s/%s.html' % (category, mid[-2], mid[-1], mid)

    @classmethod
    def get_entries_from_page(cls, page):
        entries = []

        for item in re.findall(r'class="data"[^<>]*>([^<>]+)</', page):
            song_mid = unescapeHTML(item).split('|')[-5]
            entries.append(cls.url_result(
                'http://y.qq.com/#type=song&mid=' + song_mid, 'QQMusic',
                song_mid))

        return entries


class QQMusicSingerIE(QQPlaylistBaseIE):
    _VALID_URL = r'http://y.qq.com/#type=singer&mid=(?P<id>[0-9A-Za-z]+)'
    _TEST = {
        'url': 'http://y.qq.com/#type=singer&mid=001BLpXF2DyJe2',
        'info_dict': {
            'id': '001BLpXF2DyJe2',
            'title': '林俊杰',
            'description': 'md5:2a222d89ba4455a3af19940c0481bb78',
        },
        'playlist_count': 12,
    }

    def _real_extract(self, url):
        mid = self._match_id(url)

        singer_page = self._download_webpage(
            self.qq_static_url('singer', mid), mid, 'Download singer page')

        entries = self.get_entries_from_page(singer_page)

        singer_name = self._html_search_regex(
            r"singername\s*:\s*'([^']+)'", singer_page, 'singer name',
            default=None)

        singer_id = self._html_search_regex(
            r"singerid\s*:\s*'([0-9]+)'", singer_page, 'singer id',
            default=None)

        singer_desc = None

        if singer_id:
            req = compat_urllib_request.Request(
                'http://s.plcloud.music.qq.com/fcgi-bin/fcg_get_singer_desc.fcg?utf8=1&outCharset=utf-8&format=xml&singerid=%s' % singer_id)
            req.add_header(
                'Referer', 'http://s.plcloud.music.qq.com/xhr_proxy_utf8.html')
            singer_desc_page = self._download_xml(
                req, mid, 'Donwload singer description XML')

            singer_desc = singer_desc_page.find('./data/info/desc').text

        return self.playlist_result(entries, mid, singer_name, singer_desc)


class QQMusicAlbumIE(QQPlaylistBaseIE):
    _VALID_URL = r'http://y.qq.com/#type=album&mid=(?P<id>[0-9A-Za-z]+)'

    _TEST = {
        'url': 'http://y.qq.com/#type=album&mid=000gXCTb2AhRR1&play=0',
        'info_dict': {
            'id': '000gXCTb2AhRR1',
            'title': '我们都是这样长大的',
            'description': 'md5:d216c55a2d4b3537fe4415b8767d74d6',
        },
        'playlist_count': 4,
    }

    def _real_extract(self, url):
        mid = self._match_id(url)

        album_page = self._download_webpage(
            self.qq_static_url('album', mid), mid, 'Download album page')

        entries = self.get_entries_from_page(album_page)

        album_name = self._html_search_regex(
            r"albumname\s*:\s*'([^']+)',", album_page, 'album name',
            default=None)

        album_detail = self._html_search_regex(
            r'<div class="album_detail close_detail">\s*<p>((?:[^<>]+(?:<br />)?)+)</p>',
            album_page, 'album details', default=None)

        return self.playlist_result(entries, mid, album_name, album_detail)
