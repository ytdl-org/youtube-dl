#coding: utf-8

import re

from .common import InfoExtractor
from ..utils import (
    determine_ext,
)

class ThisAVIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?thisav\.com/video/(?P<id>[0-9]+)/.*'
    _TEST = {
        u"url": u"http://www.thisav.com/video/47734/%98%26sup1%3B%83%9E%83%82---just-fit.html",
        u"file": u"47734.flv",
        u"md5": u"0480f1ef3932d901f0e0e719f188f19b",
        u"info_dict": {
            u"title": u"高樹マリア - Just fit",
            u"uploader": u"dj7970",
            u"uploader_id": u"dj7970"
        }
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)

        video_id = mobj.group('id')
        webpage = self._download_webpage(url, video_id)
        title = self._html_search_regex(r'<h1>([^<]*)</h1>', webpage, u'title')
        video_url = self._html_search_regex(
            r"addVariable\('file','([^']+)'\);", webpage, u'video url')
        uploader = self._html_search_regex(
            r': <a href="http://www.thisav.com/user/[0-9]+/(?:[^"]+)">([^<]+)</a>',
            webpage, u'uploader name', fatal=False)
        uploader_id = self._html_search_regex(
            r': <a href="http://www.thisav.com/user/[0-9]+/([^"]+)">(?:[^<]+)</a>',
            webpage, u'uploader id', fatal=False)
        ext = determine_ext(video_url)
        
        return {
            '_type':       'video',
            'id':          video_id,
            'url':         video_url,
            'uploader':    uploader,
            'uploader_id': uploader_id,
            'title':       title,
            'ext':         ext,
        }
