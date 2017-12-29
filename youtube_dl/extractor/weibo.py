# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor

import json
import random
import re

from ..compat import (
    compat_urlparse,
)
from ..utils import (
    js_to_json,
    strip_jsonp,
    urlencode_postdata,
)


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
        # to get Referer url for genvisitor
        webpage, urlh = self._download_webpage_handle(url, video_id, note="first visit the page")

        visitor_url = urlh.geturl()
        headers = {
            'Referer': visitor_url
        }

        fp = {
            "os": "2",
            "browser": "Gecko57,0,0,0",
            "fonts": "undefined",
            "screenInfo": "1440*900*24",
            "plugins": ""
        }
        data = urlencode_postdata({
            "cb": "gen_callback",
            "fp": json.dumps(fp),
        })

        genvisitor_url = 'https://passport.weibo.com/visitor/genvisitor'
        webpage, _ = self._download_webpage_handle(genvisitor_url, video_id, data=data, headers=headers, note="gen visitor")

        p = strip_jsonp(webpage)
        i1 = p.find('{')
        i2 = p.rfind('}')
        j = p[i1:i2 + 1]  # get JSON object
        d = json.loads(j)
        tid = d["data"]["tid"]
        cnfd = "%03d" % d["data"]["confidence"]

        query = {
            'a': 'incarnate',
            't': tid,
            'w': 2,
            'c': cnfd,
            'cb': 'cross_domain',
            'from': 'weibo',
            '_rand': random.random()
        }
        gencallback_url = "https://passport.weibo.com/visitor/visitor"
        self._download_webpage_handle(gencallback_url, video_id, note="gen callback", query=query)

        webpage, _ = self._download_webpage_handle(url, video_id, note="retry to visit the page")

        title = self._html_search_regex(r'<title>(.+?)</title>', webpage, 'title')

        video_sources_text = self._search_regex(r'video-sources=\\\"(.+?)\"', webpage, 'video_sources')

        video_formats = compat_urlparse.parse_qs(video_sources_text)

        formats = []
        supported_resolutions = ('720', '480')
        for res in supported_resolutions:
            f = video_formats.get(res)
            if isinstance(f, list):
                if len(f) > 0:
                    vid_url = f[0]
                    formats.append({
                        'url': vid_url,
                        'format': 'mp4',
                        'height': int(res),
                    })
        self._sort_formats(formats)
        uploader = self._og_search_property('nick-name', webpage, 'uploader', default=None)
        return {
            'id': video_id,
            'title': title,
            'uploader': uploader,
            'formats': formats
        }


class WeiboMobileIE(InfoExtractor):
    _VALID_URL = r'https?://m\.weibo\.cn/status/(?P<id>[0-9]+)(\?.+)?'
    _TEST = {
        'url': 'https://m.weibo.cn/status/4189191225395228?wm=3333_2001&sourcetype=weixin&featurecode=newtitle&from=singlemessage&isappinstalled=0',
        'info_dict': {
            'id': '4189191225395228',
            'ext': 'mp4',
            'title': '午睡当然是要甜甜蜜蜜的啦',
            'uploader': '柴犬柴犬'
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        # to get Referer url for genvisitor
        webpage, _ = self._download_webpage_handle(url, video_id, note="visit the page")
        js_code = self._search_regex(r'var\s+\$render_data\s*=\s*\[({.*})\]\[0\] \|\| {};', webpage, 'js_code', flags=re.DOTALL)
        weibo_info = self._parse_json(js_code, video_id, transform_source=js_to_json)
        page_info = weibo_info['status']['page_info']
        title = weibo_info.get('status').get('status_title')
        uploader = weibo_info.get('status').get('user').get('screen_name')

        return {
            'id': video_id,
            'title': title,
            'uploader': uploader,
            'url': page_info['media_info']['stream_url']
        }
