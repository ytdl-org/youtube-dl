# coding: utf-8
from __future__ import unicode_literals

import random
import time
import re

from .common import InfoExtractor
from ..utils import (
    sanitized_Request,
    strip_jsonp,
    unescapeHTML,
    clean_html,
    ExtractorError,
)


class QQMusicIE(InfoExtractor):
    IE_NAME = 'qqmusic'
    IE_DESC = 'QQ音乐'
    _VALID_URL = r'https?://y\.qq\.com/#type=song&mid=(?P<id>[0-9A-Za-z]+)'
    _TESTS = [{
        'url': 'http://y.qq.com/#type=song&mid=004295Et37taLD',
        'md5': '9ce1c1c8445f561506d2e3cfb0255705',
        'info_dict': {
            'id': '004295Et37taLD',
            'ext': 'mp3',
            'title': '可惜没如果',
            'release_date': '20141227',
            'creator': '林俊杰',
            'description': 'md5:d327722d0361576fde558f1ac68a7065',
            'thumbnail': r're:^https?://.*\.jpg$',
        }
    }, {
        'note': 'There is no mp3-320 version of this song.',
        'url': 'http://y.qq.com/#type=song&mid=004MsGEo3DdNxV',
        'md5': 'fa3926f0c585cda0af8fa4f796482e3e',
        'info_dict': {
            'id': '004MsGEo3DdNxV',
            'ext': 'mp3',
            'title': '如果',
            'release_date': '20050626',
            'creator': '李季美',
            'description': 'md5:46857d5ed62bc4ba84607a805dccf437',
            'thumbnail': r're:^https?://.*\.jpg$',
        }
    }, {
        'note': 'lyrics not in .lrc format',
        'url': 'http://y.qq.com/#type=song&mid=001JyApY11tIp6',
        'info_dict': {
            'id': '001JyApY11tIp6',
            'ext': 'mp3',
            'title': 'Shadows Over Transylvania',
            'release_date': '19970225',
            'creator': 'Dark Funeral',
            'description': 'md5:ed14d5bd7ecec19609108052c25b2c11',
            'thumbnail': r're:^https?://.*\.jpg$',
        },
        'params': {
            'skip_download': True,
        },
    }]

    _FORMATS = {
        'mp3-320': {'prefix': 'M800', 'ext': 'mp3', 'preference': 40, 'abr': 320},
        'mp3-128': {'prefix': 'M500', 'ext': 'mp3', 'preference': 30, 'abr': 128},
        'm4a': {'prefix': 'C200', 'ext': 'm4a', 'preference': 10}
    }

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
        if lrc_content:
            lrc_content = lrc_content.replace('\\n', '\n')

        thumbnail_url = None
        albummid = self._search_regex(
            [r'albummid:\'([0-9a-zA-Z]+)\'', r'"albummid":"([0-9a-zA-Z]+)"'],
            detail_info_page, 'album mid', default=None)
        if albummid:
            thumbnail_url = "http://i.gtimg.cn/music/photo/mid_album_500/%s/%s/%s.jpg" \
                            % (albummid[-2:-1], albummid[-1], albummid)

        guid = self.m_r_get_ruin()

        vkey = self._download_json(
            'http://base.music.qq.com/fcgi-bin/fcg_musicexpress.fcg?json=3&guid=%s' % guid,
            mid, note='Retrieve vkey', errnote='Unable to get vkey',
            transform_source=strip_jsonp)['key']

        formats = []
        for format_id, details in self._FORMATS.items():
            formats.append({
                'url': 'http://cc.stream.qqmusic.qq.com/%s%s.%s?vkey=%s&guid=%s&fromtag=0'
                       % (details['prefix'], mid, details['ext'], vkey, guid),
                'format': format_id,
                'format_id': format_id,
                'preference': details['preference'],
                'abr': details.get('abr'),
            })
        self._check_formats(formats, mid)
        self._sort_formats(formats)

        actual_lrc_lyrics = ''.join(
            line + '\n' for line in re.findall(
                r'(?m)^(\[[0-9]{2}:[0-9]{2}(?:\.[0-9]{2,})?\][^\n]*|\[[^\]]*\])', lrc_content))

        info_dict = {
            'id': mid,
            'formats': formats,
            'title': song_name,
            'release_date': publish_time,
            'creator': singer,
            'description': lrc_content,
            'thumbnail': thumbnail_url
        }
        if actual_lrc_lyrics:
            info_dict['subtitles'] = {
                'origin': [{
                    'ext': 'lrc',
                    'data': actual_lrc_lyrics,
                }]
            }
        return info_dict


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
    IE_NAME = 'qqmusic:singer'
    IE_DESC = 'QQ音乐 - 歌手'
    _VALID_URL = r'https?://y\.qq\.com/#type=singer&mid=(?P<id>[0-9A-Za-z]+)'
    _TEST = {
        'url': 'http://y.qq.com/#type=singer&mid=001BLpXF2DyJe2',
        'info_dict': {
            'id': '001BLpXF2DyJe2',
            'title': '林俊杰',
            'description': 'md5:870ec08f7d8547c29c93010899103751',
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
            req = sanitized_Request(
                'http://s.plcloud.music.qq.com/fcgi-bin/fcg_get_singer_desc.fcg?utf8=1&outCharset=utf-8&format=xml&singerid=%s' % singer_id)
            req.add_header(
                'Referer', 'http://s.plcloud.music.qq.com/xhr_proxy_utf8.html')
            singer_desc_page = self._download_xml(
                req, mid, 'Donwload singer description XML')

            singer_desc = singer_desc_page.find('./data/info/desc').text

        return self.playlist_result(entries, mid, singer_name, singer_desc)


class QQMusicAlbumIE(QQPlaylistBaseIE):
    IE_NAME = 'qqmusic:album'
    IE_DESC = 'QQ音乐 - 专辑'
    _VALID_URL = r'https?://y\.qq\.com/#type=album&mid=(?P<id>[0-9A-Za-z]+)'

    _TESTS = [{
        'url': 'http://y.qq.com/#type=album&mid=000gXCTb2AhRR1',
        'info_dict': {
            'id': '000gXCTb2AhRR1',
            'title': '我们都是这样长大的',
            'description': 'md5:179c5dce203a5931970d306aa9607ea6',
        },
        'playlist_count': 4,
    }, {
        'url': 'http://y.qq.com/#type=album&mid=002Y5a3b3AlCu3',
        'info_dict': {
            'id': '002Y5a3b3AlCu3',
            'title': '그리고...',
            'description': 'md5:a48823755615508a95080e81b51ba729',
        },
        'playlist_count': 8,
    }]

    def _real_extract(self, url):
        mid = self._match_id(url)

        album = self._download_json(
            'http://i.y.qq.com/v8/fcg-bin/fcg_v8_album_info_cp.fcg?albummid=%s&format=json' % mid,
            mid, 'Download album page')['data']

        entries = [
            self.url_result(
                'http://y.qq.com/#type=song&mid=' + song['songmid'], 'QQMusic', song['songmid']
            ) for song in album['list']
        ]
        album_name = album.get('name')
        album_detail = album.get('desc')
        if album_detail is not None:
            album_detail = album_detail.strip()

        return self.playlist_result(entries, mid, album_name, album_detail)


class QQMusicToplistIE(QQPlaylistBaseIE):
    IE_NAME = 'qqmusic:toplist'
    IE_DESC = 'QQ音乐 - 排行榜'
    _VALID_URL = r'https?://y\.qq\.com/#type=toplist&p=(?P<id>(top|global)_[0-9]+)'

    _TESTS = [{
        'url': 'http://y.qq.com/#type=toplist&p=global_123',
        'info_dict': {
            'id': 'global_123',
            'title': '美国iTunes榜',
        },
        'playlist_count': 10,
    }, {
        'url': 'http://y.qq.com/#type=toplist&p=top_3',
        'info_dict': {
            'id': 'top_3',
            'title': '巅峰榜·欧美',
            'description': 'QQ音乐巅峰榜·欧美根据用户收听行为自动生成，集结当下最流行的欧美新歌！:更新时间：每周四22点|统'
                           '计周期：一周（上周四至本周三）|统计对象：三个月内发行的欧美歌曲|统计数量：100首|统计算法：根据'
                           '歌曲在一周内的有效播放次数，由高到低取前100名（同一歌手最多允许5首歌曲同时上榜）|有效播放次数：'
                           '登录用户完整播放一首歌曲，记为一次有效播放；同一用户收听同一首歌曲，每天记录为1次有效播放'
        },
        'playlist_count': 100,
    }, {
        'url': 'http://y.qq.com/#type=toplist&p=global_106',
        'info_dict': {
            'id': 'global_106',
            'title': '韩国Mnet榜',
        },
        'playlist_count': 50,
    }]

    def _real_extract(self, url):
        list_id = self._match_id(url)

        list_type, num_id = list_id.split("_")

        toplist_json = self._download_json(
            'http://i.y.qq.com/v8/fcg-bin/fcg_v8_toplist_cp.fcg?type=%s&topid=%s&format=json'
            % (list_type, num_id),
            list_id, 'Download toplist page')

        entries = [
            self.url_result(
                'http://y.qq.com/#type=song&mid=' + song['data']['songmid'], 'QQMusic', song['data']['songmid']
            ) for song in toplist_json['songlist']
        ]

        topinfo = toplist_json.get('topinfo', {})
        list_name = topinfo.get('ListName')
        list_description = topinfo.get('info')
        return self.playlist_result(entries, list_id, list_name, list_description)


class QQMusicPlaylistIE(QQPlaylistBaseIE):
    IE_NAME = 'qqmusic:playlist'
    IE_DESC = 'QQ音乐 - 歌单'
    _VALID_URL = r'https?://y\.qq\.com/#type=taoge&id=(?P<id>[0-9]+)'

    _TESTS = [{
        'url': 'http://y.qq.com/#type=taoge&id=3462654915',
        'info_dict': {
            'id': '3462654915',
            'title': '韩国5月新歌精选下旬',
            'description': 'md5:d2c9d758a96b9888cf4fe82f603121d4',
        },
        'playlist_count': 40,
        'skip': 'playlist gone',
    }, {
        'url': 'http://y.qq.com/#type=taoge&id=1374105607',
        'info_dict': {
            'id': '1374105607',
            'title': '易入人心的华语民谣',
            'description': '民谣的歌曲易于传唱、、歌词朗朗伤口、旋律简单温馨。属于那种才入耳孔。却上心头的感觉。没有太多的复杂情绪。简单而直接地表达乐者的情绪，就是这样的简单才易入人心。',
        },
        'playlist_count': 20,
    }]

    def _real_extract(self, url):
        list_id = self._match_id(url)

        list_json = self._download_json(
            'http://i.y.qq.com/qzone-music/fcg-bin/fcg_ucc_getcdinfo_byids_cp.fcg?type=1&json=1&utf8=1&onlysong=0&disstid=%s'
            % list_id, list_id, 'Download list page',
            transform_source=strip_jsonp)
        if not len(list_json.get('cdlist', [])):
            if list_json.get('code'):
                raise ExtractorError(
                    'QQ Music said: error %d in fetching playlist info' % list_json['code'],
                    expected=True)
            raise ExtractorError('Unable to get playlist info')

        cdlist = list_json['cdlist'][0]
        entries = [
            self.url_result(
                'http://y.qq.com/#type=song&mid=' + song['songmid'], 'QQMusic', song['songmid']
            ) for song in cdlist['songlist']
        ]

        list_name = cdlist.get('dissname')
        list_description = clean_html(unescapeHTML(cdlist.get('desc')))
        return self.playlist_result(entries, list_id, list_name, list_description)
