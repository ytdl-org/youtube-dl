# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor

class CrackedIE(InfoExtractor):
    _VALID_URL = r'http?://.*?\.cracked\.com/video_+(?P<id>.*)_.*'
    _TEST = {
        'url': 'http://www.cracked.com/video_18803_4-social-criticisms-hidden-in-sonic-hedgehog-games.html',

        'info_dict': {
            'id': '18803',
            'ext': 'mp4',
            'title': "4 Social Criticisms Hidden in 'Sonic the Hedgehog' Games | Cracked.com",
            'height': 375,
            'width': 666,


        }
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')

        webpage = self._download_webpage(url, video_id)
        title = self._search_regex(r'<title>(.*?)</title>',webpage,'title')
        video_url = self._search_regex(r'var CK_vidSrc = "+(.*)"',webpage,'url')
        width = self._search_regex(r'width="(.*?)"',webpage,'width')
        height = re.findall(r'height="(.*?)"',webpage)[1]




        return {
            'url':video_url,
            'id': video_id,
            'ext':'mp4',
            'title':title,
            'height':int(height),
            'width':int(width)


        }