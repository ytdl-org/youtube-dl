# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor


class BunkrIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?((stream.bunkr\.is)|(bunkr\.su))/v/(?P<id>[0-9A-Za-z\-\.]+)'
    _TESTS = [{
        # NSFW
        'url': 'https://stream.bunkr.is/v/miera2000-(18)-xXmlmXQU.mp4',
        'info_dict': {
            'id': 'miera2000-',
            'ext': 'mp4',
            'title': 'miera2000-(18)-xXmlmXQU.mp4'
        }
    }, {
        # NSFW
        'url': 'https://bunkr.su/v/1251555_360p-1ehce9V1.mp4',
        'info_dict': {
            'id': '1251555',
            'ext': 'mp4',
            'title': '1251555_360p-1ehce9V1.mp4'
        }
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        print(webpage)
        title = self._html_search_regex(r'<title>((.|\n)+?|)</title>', webpage, 'title').split(" ")[0]
        url = self._html_search_regex(r'link.href = (.+?|);', webpage, 'url')[1:-1]
        formats = [{
            'url': url,
            'ext': 'mp4'
        }]

        return {
            'id': video_id,
            'title': title,
            'formats': formats
        }
