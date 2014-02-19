#coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import determine_ext


class ThisAVIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?thisav\.com/video/(?P<id>[0-9]+)/.*'
    _TEST = {
        'url': 'http://www.thisav.com/video/47734/%98%26sup1%3B%83%9E%83%82---just-fit.html',
        'md5': '0480f1ef3932d901f0e0e719f188f19b',
        'info_dict': {
            'id': '47734',
            'ext': 'flv',
            'title': '高樹マリア - Just fit',
            'uploader': 'dj7970',
            'uploader_id': 'dj7970'
        }
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)

        video_id = mobj.group('id')
        webpage = self._download_webpage(url, video_id)
        title = self._html_search_regex(r'<h1>([^<]*)</h1>', webpage, 'title')
        video_url = self._html_search_regex(
            r"addVariable\('file','([^']+)'\);", webpage, 'video url')
        uploader = self._html_search_regex(
            r': <a href="http://www.thisav.com/user/[0-9]+/(?:[^"]+)">([^<]+)</a>',
            webpage, 'uploader name', fatal=False)
        uploader_id = self._html_search_regex(
            r': <a href="http://www.thisav.com/user/[0-9]+/([^"]+)">(?:[^<]+)</a>',
            webpage, 'uploader id', fatal=False)
        ext = determine_ext(video_url)
        
        return {
            'id':          video_id,
            'url':         video_url,
            'uploader':    uploader,
            'uploader_id': uploader_id,
            'title':       title,
            'ext':         ext,
        }
