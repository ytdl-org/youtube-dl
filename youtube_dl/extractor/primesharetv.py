# encoding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    int_or_none,
    parse_filesize,
    unified_strdate,
    urlencode_postdata,
)
from ..compat import (
    compat_urllib_request,
)

class PrimesharetvIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?primeshare\.tv/download/(?P<id>.*)(?:.*)'

    _TESTS = [
        {
            'url': 'http://primeshare.tv/download/238790B611',
            'md5': 'bb41f9f6c0dd434c729f04ce5b677192',
            'info_dict': {
                'id': '238790B611',
                'ext': 'mp4',
                "title": "Public Domain - 1960s Commercial - Crest Toothpaste-YKsuFona [...]",
                "duration": 10,
            },
        }
    ]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)
        if re.search(r'<h1>File not exist</h1>', webpage) is not None:
            raise ExtractorError('The file does not exist', expected=True)
        hashtoken = self._search_regex(r' name="hash" value="(.*?)" ', webpage, 'hash token')
       
        self._sleep(9, video_id)
        
        data = urlencode_postdata({
            'hash': hashtoken,
        })
        headers = {
            'Referer': url,
            'Content-Type': 'application/x-www-form-urlencoded',
        }
        video_page_request = compat_urllib_request.Request(url, data, headers=headers)
        video_page = self._download_webpage(video_page_request, None, False, '')
        video_url = self._html_search_regex(
            r'url: \'(http://[a-z0-9]+\.primeshare\.tv:443/file/get/[^\']+)\',', video_page, 'video url')

        title = self._html_search_regex(
            r'<h1>Watch&nbsp;[^\(]+\(([^/)]+)\)&nbsp;', video_page, 'title')

        return {
            'id': video_id,
            'url': video_url,
            'title': title,
            'ext': 'mp4',
        }
    
    def _debug_print(self, txt):
        if self._downloader.params.get('verbose'):
            self.to_screen('[debug] %s' % txt)

