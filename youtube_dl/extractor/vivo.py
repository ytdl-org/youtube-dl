# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor

from ..compat import (
    compat_urllib_parse,
    compat_urllib_request,
)

import re

class VivoIE(InfoExtractor):
    _VALID_URL = r'http://(?:www\.)?vivo\.sx/(?P<id>[a-f0-9]{10})'
    _TEST = {
        'url': 'http://vivo.sx/d7ddda0e78',
        'md5': '2f36fed6235b16da96ce9b4dc890940d',
        'info_dict': {
            'id': 'd7ddda0e78',
            'ext': 'mp4',
            'title': 'Chicken',
            'alt_title': 'Chicken',
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        url = 'http://vivo.sx/%s' % video_id

        webpage = self._download_webpage(url, video_id)
        
        # self._sleep(7, video_id)

        headers = {
            b'Content-Type': b'application/x-www-form-urlencoded',
        }
        post = compat_urllib_parse.urlencode(self._hidden_inputs(webpage))
        req = compat_urllib_request.Request(url, post, headers)
        webpage = self._download_webpage(req, video_id, note='Downloading video page ...')

        m = re.search(r'<div class="stream-content" data-url="(?P<url>.+?)" data-name="(?P<name>.*?)(?:\.mp4)?" data-title="(?P<title>.*?)(?:\.mp4)?".*?>', webpage)

        return {
            'id': video_id,
            'title': m.group("title"),
            'alt_title': m.group("name"),
            'url' : m.group("url"),
            'ext': 'mp4',
        }
