# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..compat import (
    compat_urllib_parse_unquote,
    compat_urllib_request,
)

class ImoocVideoIE(InfoExtractor):
    _VALID_URL = r'http://www.imooc.com/video/(?P<id>[0-9]+)'
    _TEST = {
        'url': 'http://www.imooc.com/video/5454',
        'md5': '03a0f36327721551fce08776fe8f70f1',
        'info_dict': {
            'id': '5454',
            'ext': 'mp4',
            'title': '3-1 网络环境查看命令',
        }
    }

    # _ANDROID_USER_AGENT = 'Mozilla/5.0 (iPhone; U; CPU iPhone OS 4_3_3 like Mac OS X; en-us) AppleWebKit/533.17.9 (KHTML, like Gecko) Version/5.0.2 Mobile/8J2 Safari/6533.18.5'
    # _ANDROID_USER_AGENT = 'Mozilla/5.0 (X11; Linux x86_64; rv:10.0) Gecko/20150101 Firefox/20.0 (Chrome)'
    def _real_extract(self, url):
        video_id = self._match_id(url)
        # android_req = compat_urllib_request.Request(url)
        # android_req.add_header('User-Agent', self._ANDROID_USER_AGENT)
        # webpage = self._download_webpage(android_req, video_id, fatal=False)
        webpage = self._download_webpage(url, video_id)

        print webpage

        title = self._search_regex(r'var videoTitle = (.+?)', webpage, 'title')
        # title = self._search_regex(r'<span class="media-name text-ellipsis">(.+?)</span>', webpage, 'title')

        # url = self._search_regex(r'property="(.+?)"', webpage, 'url');
        url = self._search_regex(r'webkit-playsinline src="(.+?)"', webpage, 'url')
        # url = self._html_search_regex(r'<video x-webkit-airplay="allow" webkit-playsinline="" src="(.*?)"></video>', webpage, 'url')
        # <video x-webkit-airplay="allow" webkit-playsinline="" src="http://v1.mukewang.com/5495e7e0-0c1b-4d6a-9e2c-f5f145634ba0/M.mp4"></video>
        # description = self._html_search_regex(
            # r'(?s)<div class="synopsis">.*?<div class="movie_label_info"[^>]*>(.*?)</div>',
            # webpage, 'description', fatal=False)
        return {
            'id': video_id,
            'title': title,
            'url': url
        }