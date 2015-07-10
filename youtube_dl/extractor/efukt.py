# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import str_to_int

import re


class EfuktIE(InfoExtractor):
    _VALID_URL = r'(?:http://)?(?:www\.)?efukt\.com/(?P<id>[0-9]+)(?:_[^_.]+)+\.html'
    _TEST = {
        'url': 'http://efukt.com/21269_Epic_2_Horrible_in_Thirty_Seconds!.html',
        'md5': 'f07f2f58ae29dc01ce7351e4e825797f',
        'info_dict': {
            'id': '21269',
            'ext': 'mp4',
            'thumbnail': 'http://assets.efukt.com/player-preview/21269.mp4.jpg',
            'format': 'mp4',
            'title': 'Epic 2 Horrible in Thirty Seconds!',
            'description': "She pretty much aces the whole 'prostitute on camera' thing except for one small detail: This newbie pornstar's lady cum has a really unique... consistency. LOLOLOLOLOLOLOLOLOLOL. Full Vid HERE."
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)

        if(re.match(r'http://', url) is None):
            url = 'http://' + url

        webpage = self._download_webpage(url, video_id)

        title = self._html_search_meta('og:title', webpage, 'title')
        video_url = self._html_search_regex(r'file:\s?"(?P<video_url>(?:http://)?(?:www\.)?assets\.efukt\.com/videos/(?:[^.]+)\.(mp4|flv))"', webpage, 'video_url')
        thumbnail = self._html_search_meta('og:image', webpage, 'thumbnail', fatal=False)
        description = self._html_search_meta('og:description', webpage, 'description', fatal=False)
        view_count = self._html_search_regex(r'<i class="fa fa-play-circle-o"></i>&nbsp;&nbsp;(?P<view_count>(?:[0-9]+,?)+)', webpage, 'view_count', fatal=False)

        if view_count:
            view_count = str_to_int(view_count)

        return {
            'id': video_id,
            'url': video_url,
            'title': title,
            'thumbnail': thumbnail,
            'description': description,
            'ext': 'mp4',
            'format': 'mp4',
            'view_count': view_count
        }
