# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..compat import compat_urllib_parse_unquote

class ManyVidsIE(InfoExtractor):
    _VALID_URL = r'https?://www.manyvids\.com/Video/(?P<id>[0-9]+)'
    _TEST = {
        'url': 'https://www.manyvids.com/Video/133957/everthing-about-me/',
        'md5': '03f11bb21c52dd12a05be21a5c7dcc97',
        'info_dict': {
            'id': '133957',
            'ext': 'mp4',
            'title': 'everthing about me',

        }
    }

    def _real_extract(self, url):
        formats = []
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)
        video_url = compat_urllib_parse_unquote(self._search_regex(
            r'data-video-filepath=\"(.+?)\"', webpage, 'video URL', default=''))

        title = self._html_search_regex(r'<h2 class="m-a-0" title=\"(.+?)\">',
                                              webpage, 'title')
        formats.append({
            'url': video_url
        })
        return {
            'id': video_id,
            'title': title,
            'formats': formats,

        }