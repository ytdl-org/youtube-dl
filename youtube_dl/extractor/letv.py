# coding: utf-8
from __future__ import unicode_literals

import datetime
import re
import time

from .common import InfoExtractor
from ..compat import (
    compat_urllib_parse,
    compat_urllib_request,
    compat_urlparse,
)
from ..utils import (
    determine_ext,
    ExtractorError,
    parse_iso8601,
    int_or_none,
)


class LetvIE(InfoExtractor):
    IE_DESC = '乐视网'
    _VALID_URL = r'http://www\.letv\.com/ptv/vplay/(?P<id>\d+).html'

    _TESTS = [{
        'url': 'http://www.letv.com/ptv/vplay/22005890.html',
        'md5': 'cab23bd68d5a8db9be31c9a222c1e8df',
        'info_dict': {
            'id': '22005890',
            'ext': 'mp4',
            'title': '第87届奥斯卡颁奖礼完美落幕 《鸟人》成最大赢家',
            'timestamp': 1424747397,
            'upload_date': '20150224',
            'description': 'md5:a9cb175fd753e2962176b7beca21a47c',
        }
    }, {
        'url': 'http://www.letv.com/ptv/vplay/1415246.html',
        'info_dict': {
            'id': '1415246',
            'ext': 'mp4',
            'title': '美人天下01',
            'description': 'md5:f88573d9d7225ada1359eaf0dbf8bcda',
        },
    }, {
        'note': 'This video is available only in Mainland China, thus a proxy is needed',
        'url': 'http://www.letv.com/ptv/vplay/1118082.html',
        'md5': 'f80936fbe20fb2f58648e81386ff7927',
        'info_dict': {
            'id': '1118082',
            'ext': 'mp4',
            'title': '与龙共舞 完整版',
            'description': 'md5:7506a5eeb1722bb9d4068f85024e3986',
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
        play_json_req = compat_urllib_request.Request(
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

                # Mimic what flvxz.com do
                url_parts = list(compat_urlparse.urlparse(media_url))
                qs = dict(compat_urlparse.parse_qs(url_parts[4]))
                qs.update({
                    'platid': '14',
                    'splatid': '1401',
                    'tss': 'no',
                    'retry': 1
                })
                url_parts[4] = compat_urllib_parse.urlencode(qs)
                media_url = compat_urlparse.urlunparse(url_parts)

                url_info_dict = {
                    'url': media_url,
                    'ext': determine_ext(dispatch[format_id][1]),
                    'format_id': format_id,
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
