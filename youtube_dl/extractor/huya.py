# coding: utf-8
from __future__ import unicode_literals

import json
import re

from youtube_dl.utils import ExtractorError
from .common import InfoExtractor


class HuyaIE(InfoExtractor):
    _VALID_URL = r'https?://www\.huya\.com/(?P<id>\w+)'
    _TEST = {
        'url': 'https://www.huya.com/100270',
        'md5': 'e2434de1928900a03bc2bd7f819c0df1',
        'info_dict': {
            'id': '100270',
            'ext': 'flv',
            'title': '瓦莉拉炉石传说直播_瓦莉拉视频直播 - 虎牙直播',
            'description': '虎牙瓦莉拉炉石传说直播，瓦莉拉与您分享炉石传说游戏乐趣。',
            'uploader': '瓦莉拉',
            'thumbnail': r're:^https?://.*\.jpg$',
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)
        title = self._html_search_regex(r'<title>(.+?)</title>', webpage, 'title')
        info = self._get_info(webpage)
        ret = {
            'id': video_id,
            'title': title,
            'description': self._html_search_meta('description', webpage),
            'uploader': self._html_search_regex(r'class="host-name" title="(.+?)">', webpage, 'uploader'),
            'url': info[0],
            'thumbnail': info[1]
        }
        return ret

    def _get_info(self, webpage):

        try:
            p = re.compile(r'var hyPlayerConfig = (.*?);', flags=re.S | re.M)
            s = re.search(p, webpage)
            s = json.loads(s.group(1))
            if not s.get('stream'):
                raise ExtractorError('主播已下线！')
        except AttributeError:
            raise ExtractorError('May wrong URL, pls check ...')

        s_info = s['stream']['data'][0]['gameStreamInfoList']
        screen_shot = s['stream']['data'][0]['gameLiveInfo']['screenshot']
        ret = []
        for j in s_info:
            s_flv_url = j.get('sFlvUrl')
            s_stream_name = j.get('sStreamName')
            s_flv_anti_code = j.get('sFlvAntiCode')
            ret_url = '{}/{}.flv?{}&ratio=5000'.format(s_flv_url, s_stream_name, s_flv_anti_code)
            ret.append(ret_url)
        return ret[0], screen_shot
