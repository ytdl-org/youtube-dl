# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    compat_urllib_parse,
    compat_urllib_request,
)


class AllmyvideosIE(InfoExtractor):
    IE_NAME = 'allmyvideos.net'
    _VALID_URL = r'https?://allmyvideos\.net/(?P<id>[a-zA-Z0-9_-]+)'

    _TEST = {
        'url': 'http://allmyvideos.net/jih3nce3x6wn',
        'md5': '8f26c1e7102556a0d7f24306d32c2092',
        'info_dict': {
            'id': 'jih3nce3x6wn',
            'ext': 'mp4',
            'title': 'youtube-dl test video',
        },
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')

        orig_webpage = self._download_webpage(url, video_id)
        fields = re.findall(r'type="hidden" name="(.+?)"\s* value="?(.+?)">', orig_webpage)
        data = {}
        for name, value in fields:
            data[name] = value

        post = compat_urllib_parse.urlencode(data)
        headers = {
            b'Content-Type': b'application/x-www-form-urlencoded',
        }
        req = compat_urllib_request.Request(url, post, headers)
        webpage = self._download_webpage(req, video_id, note='Downloading video page ...')

        #Could be several links with different quality
        links = re.findall(r'"file" : "?(.+?)",', webpage)

        return {
            'id': video_id,
            'title': data['fname'][:len(data['fname'])-4],  #Remove .mp4 extension
            'url': links[len(links)-1]                      #Choose the higher quality link
        }