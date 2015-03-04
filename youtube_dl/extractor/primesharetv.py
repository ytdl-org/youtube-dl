# encoding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import (
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

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)
       
        self._sleep(9, video_id)
        
        hashtoken = self._search_regex(r' name="hash" value="(.*?)" ', webpage, 'hash token')
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
            r'url: \'(http://l\.primeshare\.tv[^\']+)\',', video_page, 'video url')

        title = self._html_search_regex(
            r'<h1>Watch&nbsp;[^\(]+\(([^/)]+)\)&nbsp;', video_page, 'title')

        return {
            'id': video_id,
            'url': video_url,
            'title': title,
            'ext': 'mp4',
        }
