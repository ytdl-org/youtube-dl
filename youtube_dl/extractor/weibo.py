# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor

from urllib.request import Request
from urllib.parse import urlencode
from urllib import parse
import json
import random as rnd
from os import path

class WeiboIE(InfoExtractor):
    _VALID_URL = r'https?://weibo\.com/[0-9]+/(?P<id>[a-zA-Z0-9]+)'
    _TEST = {
            'url': 'https://weibo.com/6275294458/Fp6RGfbff?type=comment',
            'info_dict': {
                'id': 'Fp6RGfbff',
                'ext': 'mp4',
                'title': 'You should have servants to massage you,... 来自Hosico_猫 - 微博',
                }
            }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'en,zh-CN;q=0.9,zh;q=0.8',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.84 Safari/537.36',
            'Upgrade-Insecure-Requests': '1',
        }
        # to get Referer url for genvisitor
        webpage,urlh = self._download_webpage_handle(url, video_id, headers=headers, note="first visit the page")

        visitor_url = urlh.geturl()

        data = urlencode({
            "cb": "gen_callback",
            "fp": '{"os":"2","browser":"Gecko57,0,0,0","fonts":"undefined","screenInfo":"1440*900*24","plugins":""}',
            }).encode()
        headers = {
                'Accept-Encoding': 'gzip, deflate, br',
                'Accept': '*/*',
                'Referer': visitor_url,
                }

        r_genvisitor = Request(
            'https://passport.weibo.com/visitor/genvisitor',
            data = data,
            headers = headers,
            method = 'POST'
            )
        webpage,urlh = self._download_webpage_handle(r_genvisitor, video_id, note="gen visitor")
        print("webpage", webpage)

        p = webpage.split("&&")[1] # split "gen_callback && gen_callback(...)"
        i1 = p.find('{')
        i2 = p.rfind('}')
        j = p[i1:i2+1] # get JSON object
        d = json.loads(j)
        tid = d["data"]["tid"]
        cnfd = "%03d" % d["data"]["confidence"]

        param = urlencode({
            'a': 'incarnate',
            't': tid,
            'w': 2,
            'c': cnfd,
            'cb': 'cross_domain',
            'from': 'weibo',
            '_rand': rnd.random()
            })
        gencallback_url = "https://passport.weibo.com/visitor/visitor?" + param
        webpage,urlh = self._download_webpage_handle(gencallback_url, video_id, note="gen callback")

        webpage,urlh = self._download_webpage_handle(url, video_id, headers=headers, note="retry to visit the page")

        # TODO more code goes here, for example ...
        title = self._html_search_regex(r'<title>(.+?)</title>', webpage, 'title')

        video_sources_text = self._search_regex("video-sources=\\\\\"(.+?)\"", webpage, 'video_sources')
        
        video_formats = parse.parse_qs(video_sources_text)

        formats = []
        supported_resolutions = ['720', '480']
        for res in supported_resolutions:
            f = video_formats.get(res)
            if isinstance(f, list):
                if len(f) > 0:
                    vid_url = f[0]
                    print("%s:%s" % (res, vid_url))
                    formats.append({
                        'url': vid_url
                        })
        self._sort_formats(formats)
        uploader = self._og_search_property('nick-name', webpage, 'uploader', default = None)
        print(title, uploader)
        return {
                'id': video_id,
                'title': title,
                'uploader': uploader,
                'formats': formats
                # TODO more properties (see youtube_dl/extractor/common.py)
                }
