# coding: utf-8
from __future__ import unicode_literals

import datetime
import re
import time
import base64
import hashlib

from .common import InfoExtractor
from ..compat import (
    compat_urllib_parse,
    compat_ord,
    compat_str,
)
from ..utils import (
    determine_ext,
    ExtractorError,
    parse_iso8601,
    sanitized_Request,
    int_or_none,
    str_or_none,
    encode_data_uri,
    url_basename,
)


class LetvIE(InfoExtractor):
    IE_DESC = '乐视网'
    _VALID_URL = r'http://www\.letv\.com/ptv/vplay/(?P<id>\d+).html'

    _TESTS = [{
        'url': 'http://www.letv.com/ptv/vplay/22005890.html',
        'md5': 'edadcfe5406976f42f9f266057ee5e40',
        'info_dict': {
            'id': '22005890',
            'ext': 'mp4',
            'title': '第87届奥斯卡颁奖礼完美落幕 《鸟人》成最大赢家',
            'description': 'md5:a9cb175fd753e2962176b7beca21a47c',
        },
        'params': {
            'hls_prefer_native': True,
        },
    }, {
        'url': 'http://www.letv.com/ptv/vplay/1415246.html',
        'info_dict': {
            'id': '1415246',
            'ext': 'mp4',
            'title': '美人天下01',
            'description': 'md5:f88573d9d7225ada1359eaf0dbf8bcda',
        },
        'params': {
            'hls_prefer_native': True,
        },
    }, {
        'note': 'This video is available only in Mainland China, thus a proxy is needed',
        'url': 'http://www.letv.com/ptv/vplay/1118082.html',
        'md5': '2424c74948a62e5f31988438979c5ad1',
        'info_dict': {
            'id': '1118082',
            'ext': 'mp4',
            'title': '与龙共舞 完整版',
            'description': 'md5:7506a5eeb1722bb9d4068f85024e3986',
        },
        'params': {
            'hls_prefer_native': True,
        },
        'skip': 'Only available in China',
    }]

    @staticmethod
    def urshift(val, n):
        return val >> n if val >= 0 else (val + 0x100000000) >> n

    # ror() and calc_time_key() are reversed from a embedded swf file in KLetvPlayer.swf
    def ror(self, param1, param2):
        _loc3_ = 0
        while _loc3_ < param2:
            param1 = self.urshift(param1, 1) + ((param1 & 1) << 31)
            _loc3_ += 1
        return param1

    def calc_time_key(self, param1):
        _loc2_ = 773625421
        _loc3_ = self.ror(param1, _loc2_ % 13)
        _loc3_ = _loc3_ ^ _loc2_
        _loc3_ = self.ror(_loc3_, _loc2_ % 17)
        return _loc3_

    # see M3U8Encryption class in KLetvPlayer.swf
    @staticmethod
    def decrypt_m3u8(encrypted_data):
        if encrypted_data[:5].decode('utf-8').lower() != 'vc_01':
            return encrypted_data
        encrypted_data = encrypted_data[5:]

        _loc4_ = bytearray()
        while encrypted_data:
            b = compat_ord(encrypted_data[0])
            _loc4_.extend([b // 16, b & 0x0f])
            encrypted_data = encrypted_data[1:]
        idx = len(_loc4_) - 11
        _loc4_ = _loc4_[idx:] + _loc4_[:idx]
        _loc7_ = bytearray()
        while _loc4_:
            _loc7_.append(_loc4_[0] * 16 + _loc4_[1])
            _loc4_ = _loc4_[2:]

        return bytes(_loc7_)

    def _real_extract(self, url):
        media_id = self._match_id(url)
        page = self._download_webpage(url, media_id)
        params = {
            'id': media_id,
            'platid': 1,
            'splatid': 101,
            'format': 1,
            'tkey': self.calc_time_key(int(time.time())),
            'domain': 'www.letv.com'
        }
        play_json_req = sanitized_Request(
            'http://api.letv.com/mms/out/video/playJson?' + compat_urllib_parse.urlencode(params)
        )
        cn_verification_proxy = self._downloader.params.get('cn_verification_proxy')
        if cn_verification_proxy:
            play_json_req.add_header('Ytdl-request-proxy', cn_verification_proxy)

        play_json = self._download_json(
            play_json_req,
            media_id, 'Downloading playJson data')

        # Check for errors
        playstatus = play_json['playstatus']
        if playstatus['status'] == 0:
            flag = playstatus['flag']
            if flag == 1:
                msg = 'Country %s auth error' % playstatus['country']
            else:
                msg = 'Generic error. flag = %d' % flag
            raise ExtractorError(msg, expected=True)

        playurl = play_json['playurl']

        formats = ['350', '1000', '1300', '720p', '1080p']
        dispatch = playurl['dispatch']

        urls = []
        for format_id in formats:
            if format_id in dispatch:
                media_url = playurl['domain'][0] + dispatch[format_id][0]
                media_url += '&' + compat_urllib_parse.urlencode({
                    'm3v': 1,
                    'format': 1,
                    'expect': 3,
                    'rateid': format_id,
                })

                nodes_data = self._download_json(
                    media_url, media_id,
                    'Download JSON metadata for format %s' % format_id)

                req = self._request_webpage(
                    nodes_data['nodelist'][0]['location'], media_id,
                    note='Downloading m3u8 information for format %s' % format_id)

                m3u8_data = self.decrypt_m3u8(req.read())

                url_info_dict = {
                    'url': encode_data_uri(m3u8_data, 'application/vnd.apple.mpegurl'),
                    'ext': determine_ext(dispatch[format_id][1]),
                    'format_id': format_id,
                    'protocol': 'm3u8',
                }

                if format_id[-1:] == 'p':
                    url_info_dict['height'] = int_or_none(format_id[:-1])

                urls.append(url_info_dict)

        publish_time = parse_iso8601(self._html_search_regex(
            r'发布时间&nbsp;([^<>]+) ', page, 'publish time', default=None),
            delimiter=' ', timezone=datetime.timedelta(hours=8))
        description = self._html_search_meta('description', page, fatal=False)

        return {
            'id': media_id,
            'formats': urls,
            'title': playurl['title'],
            'thumbnail': playurl['pic'],
            'description': description,
            'timestamp': publish_time,
        }


class LetvTvIE(InfoExtractor):
    _VALID_URL = r'http://www.letv.com/tv/(?P<id>\d+).html'
    _TESTS = [{
        'url': 'http://www.letv.com/tv/46177.html',
        'info_dict': {
            'id': '46177',
            'title': '美人天下',
            'description': 'md5:395666ff41b44080396e59570dbac01c'
        },
        'playlist_count': 35
    }]

    def _real_extract(self, url):
        playlist_id = self._match_id(url)
        page = self._download_webpage(url, playlist_id)

        media_urls = list(set(re.findall(
            r'http://www.letv.com/ptv/vplay/\d+.html', page)))
        entries = [self.url_result(media_url, ie='Letv')
                   for media_url in media_urls]

        title = self._html_search_meta('keywords', page,
                                       fatal=False).split('，')[0]
        description = self._html_search_meta('description', page, fatal=False)

        return self.playlist_result(entries, playlist_id, playlist_title=title,
                                    playlist_description=description)


class LetvPlaylistIE(LetvTvIE):
    _VALID_URL = r'http://tv.letv.com/[a-z]+/(?P<id>[a-z]+)/index.s?html'
    _TESTS = [{
        'url': 'http://tv.letv.com/izt/wuzetian/index.html',
        'info_dict': {
            'id': 'wuzetian',
            'title': '武媚娘传奇',
            'description': 'md5:e12499475ab3d50219e5bba00b3cb248'
        },
        # This playlist contains some extra videos other than the drama itself
        'playlist_mincount': 96
    }, {
        'url': 'http://tv.letv.com/pzt/lswjzzjc/index.shtml',
        'info_dict': {
            'id': 'lswjzzjc',
            # The title should be "劲舞青春", but I can't find a simple way to
            # determine the playlist title
            'title': '乐视午间自制剧场',
            'description': 'md5:b1eef244f45589a7b5b1af9ff25a4489'
        },
        'playlist_mincount': 7
    }]


class LetvCloudIE(InfoExtractor):
    IE_DESC = '乐视云'
    _VALID_URL = r'https?://yuntv\.letv\.com/bcloud.html\?.+'

    _TESTS = [{
        'url': 'http://yuntv.letv.com/bcloud.html?uu=p7jnfw5hw9&vu=467623dedf',
        'md5': '26450599afd64c513bc77030ad15db44',
        'info_dict': {
            'id': 'p7jnfw5hw9_467623dedf',
            'ext': 'mp4',
            'title': 'Video p7jnfw5hw9_467623dedf',
        },
    }, {
        'url': 'http://yuntv.letv.com/bcloud.html?uu=p7jnfw5hw9&vu=ec93197892&pu=2c7cd40209&auto_play=1&gpcflag=1&width=640&height=360',
        'md5': 'e03d9cc8d9c13191e1caf277e42dbd31',
        'info_dict': {
            'id': 'p7jnfw5hw9_ec93197892',
            'ext': 'mp4',
            'title': 'Video p7jnfw5hw9_ec93197892',
        },
    }, {
        'url': 'http://yuntv.letv.com/bcloud.html?uu=p7jnfw5hw9&vu=187060b6fd',
        'md5': 'cb988699a776b22d4a41b9d43acfb3ac',
        'info_dict': {
            'id': 'p7jnfw5hw9_187060b6fd',
            'ext': 'mp4',
            'title': 'Video p7jnfw5hw9_187060b6fd',
        },
    }]

    @staticmethod
    def sign_data(obj):
        if obj['cf'] == 'flash':
            salt = '2f9d6924b33a165a6d8b5d3d42f4f987'
            items = ['cf', 'format', 'ran', 'uu', 'ver', 'vu']
        elif obj['cf'] == 'html5':
            salt = 'fbeh5player12c43eccf2bec3300344'
            items = ['cf', 'ran', 'uu', 'bver', 'vu']
        input_data = ''.join([item + obj[item] for item in items]) + salt
        obj['sign'] = hashlib.md5(input_data.encode('utf-8')).hexdigest()

    def _get_formats(self, cf, uu, vu, media_id):
        def get_play_json(cf, timestamp):
            data = {
                'cf': cf,
                'ver': '2.2',
                'bver': 'firefox44.0',
                'format': 'json',
                'uu': uu,
                'vu': vu,
                'ran': compat_str(timestamp),
            }
            self.sign_data(data)
            return self._download_json(
                'http://api.letvcloud.com/gpc.php?' + compat_urllib_parse.urlencode(data),
                media_id, 'Downloading playJson data for type %s' % cf)

        play_json = get_play_json(cf, time.time())
        # The server time may be different from local time
        if play_json.get('code') == 10071:
            play_json = get_play_json(cf, play_json['timestamp'])

        if not play_json.get('data'):
            if play_json.get('message'):
                raise ExtractorError('Letv cloud said: %s' % play_json['message'], expected=True)
            elif play_json.get('code'):
                raise ExtractorError('Letv cloud returned error %d' % play_json['code'], expected=True)
            else:
                raise ExtractorError('Letv cloud returned an unknwon error')

        def b64decode(s):
            return base64.b64decode(s.encode('utf-8')).decode('utf-8')

        formats = []
        for media in play_json['data']['video_info']['media'].values():
            play_url = media['play_url']
            url = b64decode(play_url['main_url'])
            decoded_url = b64decode(url_basename(url))
            formats.append({
                'url': url,
                'ext': determine_ext(decoded_url),
                'format_id': int_or_none(play_url.get('vtype')),
                'format_note': str_or_none(play_url.get('definition')),
                'width': int_or_none(play_url.get('vwidth')),
                'height': int_or_none(play_url.get('vheight')),
            })

        return formats

    def _real_extract(self, url):
        uu_mobj = re.search('uu=([\w]+)', url)
        vu_mobj = re.search('vu=([\w]+)', url)

        if not uu_mobj or not vu_mobj:
            raise ExtractorError('Invalid URL: %s' % url, expected=True)

        uu = uu_mobj.group(1)
        vu = vu_mobj.group(1)
        media_id = uu + '_' + vu

        formats = self._get_formats('flash', uu, vu, media_id) + self._get_formats('html5', uu, vu, media_id)
        self._sort_formats(formats)

        return {
            'id': media_id,
            'title': 'Video %s' % media_id,
            'formats': formats,
        }
