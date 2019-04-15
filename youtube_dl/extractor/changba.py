# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor

import re

class ChangbaIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?changba\.com/s/(?P<id>[0-9A-Za-z-_]+)'
    _TESTS = [{
        'url': 'https://changba.com/s/0GHVw6vyXv9N2FhaFi2WJg',
        'md5': 'ea55d17e939f3e2dabf483e47e8e5693',
        'info_dict': {
            'id': '1152860688',
            'ext': 'mp4',
            'title': '对你爱不完【炫酷慢摇】 ',
            # 'thumbnail': r're:^https?://.*\.jpg$',
            # TODO more properties, either as:
            # * A value
            # * MD5 checksum; start the string with md5:
            # * A regular expression; start the string with re:
            # * Any Python type (for example int or float)
        }
    },
    {
        'url': 'http://changba.com/s/nZqfbS_vCnieNNjJ7UiEGw?',
        'md5': 'e401463ffb03ed8900a0bccc641335e1',
        'info_dict': {
            'id': '1091968526',
            'ext': 'mp3',
            'title': '下雪 ',
        }
    },
    {
        'url': 'http://changba.com/s/CPiNWbAa1qy0po0llqIJbg',
        'md5': '',
        'info_dict': {
            'id': '136918054',
            'ext': 'mp3',
            'title': '红豆 ',
        }
    },
    {
        'url': 'http://changba.com/s/-N00JJ30YruunrER5eBcWw',
        'md5': 'cd68f8da8d8c69afbb8e4dbbbfa8b277',
        'info_dict': {
            'id': '172671761',
            'ext': 'mp3',
            'title': '天与地 ',
        }
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)
        id = self._search_regex(r'workid=([0-9]+)', webpage, 'id')
        isvideo = self._search_regex(r'&isvideo=([0-9])', webpage, 'isvideo')
        title = self._search_regex(r'<div[^>]+class="title"[^>]*>([^<]+)', webpage, 'title')

        ext = "mp4"
        if int(isvideo) == 0:
            ext = "mp3"
        
        try:
            url = self._search_regex(r'([a-z]+:\/\/[0-9a-z]+\.changba\.com\/[a-z]+\/[a-z]+\/[0-9]+\/[0-9]+\.mp[3-4])', webpage, 'url')
        except:
            url = "http://lzscuw.changba.com/" + str(id) + "." + ext

        return {
            'url': url,
            'id': id,
            'ext': ext,
            'title': title
        }
