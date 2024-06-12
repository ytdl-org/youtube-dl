# coding: utf-8
from __future__ import unicode_literals

from datetime import datetime
import re

from .common import InfoExtractor
from ..utils import orderedSet


class KuaishouIE(InfoExtractor):
    _VALID_URL = r'https?://live\.kuaishou\.com/u/[a-zA-Z0-9]+/(?P<id>[a-z0-9]+)\?did=(?P<d_id>web_[a-zA-Z0-9]+)'
    _TEST = {
        'url': 'https://live.kuaishou.com/u/jjworld126/3xajmx3ayxnsut4?did=web_5eb8e90590774dc5b99d5af119be9911',
        'md5': '73996963def08727f536a4a0cd030225',
        'info_dict': {
            'id': '3xajmx3ayxnsut4',
            'url': 'http://jsmov2.a.yximgs.com/bs2/newWatermark/MjEwMjIwNTk0MTU_zh_4.mp4',
            'title': '#快影 神农配合，总冠军牛牛牛。#斗地主 #电竞梦 #每个人都有自己的奋斗',
            'thumbnail': 'http://js2.a.yximgs.com/upic/2019/12/28/19/BMjAxOTEyMjgxOTAwNTlfOTY3Mzk5MjI3XzIxMDIyMDU5NDE1XzFfMw==_Be9263b19ab4c41603ea7cbb5be834169.jpg',
            'timestamp': 1577530862.302,
            'upload_date': '20191228',
            'ext': 'mp4',
        }
    }

    def _real_extract(self, url):
        video_id, d_id = re.match(self._VALID_URL, url).groups()
        d_idv = (int(datetime.now().timestamp()) - 15 * 60) * 1000
        headers = {'Cookie': 'did=%s; didv=%s' % (d_id, d_idv)}
        webpage = self._download_webpage(url, video_id, headers=headers)
        video_feed_json = self._search_regex(r'"VideoFeed:%s":(.*),"\$VideoFeed:%s.counts"' % (video_id, video_id), webpage, 'video_feed')
        video_feed = self._parse_json(video_feed_json, video_id)

        return {
            'id': video_feed['id'],
            'url': video_feed['playUrl'],
            'title': video_feed['caption'],
            'thumbnail': video_feed['thumbnailUrl'],
            'timestamp': video_feed['timestamp'] / 1000,
        }


class KuaishouProfileIE(InfoExtractor):
    _VALID_URL = r'https?://live\.kuaishou\.com/profile/(?P<id>[a-zA-Z0-9\-]+)\?did=(?P<d_id>web_[a-zA-Z0-9]+)'
    _TEST = {
        'url': 'https://live.kuaishou.com/profile/jjworld126?did=web_5da4e11838fc2152269bf983bd8180bc',
        'info_dict': {
            'id': 'jjworld126',
        },
        'playlist_mincount': 24,
    }

    def _real_extract(self, url):
        profile_id, d_id = re.match(self._VALID_URL, url).groups()
        d_idv = (int(datetime.now().timestamp()) - 15 * 60) * 1000
        headers = {'Cookie': 'did=%s, didv=%s, clientid=%s, client_key=%s, kuaishou.live.bfb1s=%s' % (d_id, d_idv, 3, '65890b29', '3e261140b0cf7444a0ba411c6f227d88')}
        webpage = self._download_webpage(url, profile_id, headers=headers)
        profile_feeds_json = self._search_regex(r'({"pcursor":.*,"__typename":"PCProfileFeeds"})', webpage, 'profile_feeds')
        profile_feeds = self._parse_json(profile_feeds_json, profile_id)

        entries = [
            self.url_result('https://live.kuaishou.com/u/%s/%s?did=%s' % (profile_id, video_id, d_id), KuaishouIE.ie_key(), video_id)
            for video_id in [video_feed['id'].split(':')[1] for video_feed in profile_feeds['list']]
        ]

        return self.playlist_result(orderedSet(entries), profile_id)
