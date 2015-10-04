# http://qianmo.com/bazingayue/324
# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from lxml import html
import requests

import re


class QianmoIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?qianmo\.com/(?P<user>[A-Za-z]+)/(?P<id>[0-9]+)'
    _TEST = {
        'url': 'http://qianmo.com/kawaei/281',
        'info_dict': {
            'id': '281',
            'ext': 'mp4',
            'title': '[中字] Google新logo宣传片 「Google, 进化」 - 阡陌视频社区',
            # TODO more properties, either as:
            # * A value
            # * MD5 checksum; start the string with md5:
            # * A regular expression; start the string with re:
            # * Any Python type (for example int or float)
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)

        webpage = self._download_webpage(url, video_id)
        title = self._html_search_regex(r'<title>(.*?)</title>', webpage, 'title')
        
        video_url = self._html_search_regex(r'"urls":\["(.*?)"\],', webpage, 'url')
        

        return {
            'id': video_id,
            'title': title,
            'url': video_url,
            'ext': 'mp4',
            # TODO more properties (see youtube_dl/extractor/common.py)
        }