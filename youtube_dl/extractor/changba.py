# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor

import re

class ChangbaIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?changba\.com/s/(?P<id>[0-9A-Za-z-_]+)'
    _TEST = {
        'url': 'https://changba.com/s/0GHVw6vyXv9N2FhaFi2WJg',
        'md5': 'TODO: md5 sum of the first 10241 bytes of the video file (use --test)',
        'info_dict': {
            'id': '1152860688',
            'ext': 'mp4',
            'title': 'Video title goes here',
            'thumbnail': r're:^https?://.*\.jpg$',
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
        id = self._search_regex(r'workid=([0-9]+)', webpage, 'id')
        isvideo = self._search_regex(r'&isvideo=([0-9])', webpage, 'isvideo')
        title = self._search_regex(r'<div[^>]+class="title"[^>]*>([^<]+)', webpage, 'title')

        if int(isvideo) == 0:
            ext = 'mp3'
            try:
                url = self._search_regex(r'([a-z]+:\/\/[0-9a-z]+\.changba\.com\/[a-z]+\/[a-z]+\/[0-9]+\/[0-9]+\.mp3)', webpage, 'url')
            except:
                url = "http://lzscuw.changba.com/" + str(id) + ".mp3"
        else:
            ext = 'mp4'
            try:
                url = self._search_regex(r'([a-z]+:\/\/[0-9a-z]+\.changba\.com\/[a-z]+\/[a-z]+\/[0-9]+\/[0-9]+\.mp4)', webpage, 'url')
            except:
                url = "http://lzscuw.changba.com/" + str(id) + ".mp4"

        return {
            'url': url,
            'id': id,
            'ext': ext,
            'title': title
        }
