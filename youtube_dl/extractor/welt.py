from __future__ import unicode_literals

import re

from .common import InfoExtractor

class WeltIE(InfoExtractor):
    IE_NAME = 'welt.de'
    _VALID_URL = r'''https?://(?:www\.)?welt\.de/mediathek/dokumentation/.*sendung(?P<id>\d+)/.*'''
    _TESTS = [
        {
            'url': 'https://www.welt.de/mediathek/dokumentation/space/sendung170058475/ISS-Leben-auf-der-Weltraumstation.html',
            'info_dict': {
                'ext': 'mp4',
                'title': 'ISS - Leben auf der Weltraumstation',
            }
        }
    ]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)
        title = self._html_search_regex(r'<title>([^<]+)</title>', webpage, 'title')
        video_url = self._html_search_regex(r'<source data-content="Video.source" src="(https://weltn24.+?_2000.mp4)"', webpage, 'video_url')

        return [{
            'id':   video_id,
            'url':  video_url,
            'ext':  'mp4',
            'title': title,
        }]
