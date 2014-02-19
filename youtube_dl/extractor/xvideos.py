from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    compat_urllib_parse,
)


class XVideosIE(InfoExtractor):
    _VALID_URL = r'^(?:https?://)?(?:www\.)?xvideos\.com/video([0-9]+)(?:.*)'
    _TEST = {
        'url': 'http://www.xvideos.com/video939581/funny_porns_by_s_-1',
        'file': '939581.flv',
        'md5': '1d0c835822f0a71a7bf011855db929d0',
        'info_dict': {
            "title": "Funny Porns By >>>>S<<<<<< -1",
            "age_limit": 18,
        }
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group(1)

        webpage = self._download_webpage(url, video_id)

        self.report_extraction(video_id)

        # Extract video URL
        video_url = compat_urllib_parse.unquote(
            self._search_regex(r'flv_url=(.+?)&', webpage, 'video URL'))

        # Extract title
        video_title = self._html_search_regex(
            r'<title>(.*?)\s+-\s+XVID', webpage, 'title')

        # Extract video thumbnail
        video_thumbnail = self._search_regex(
            r'url_bigthumb=(.+?)&amp', webpage, 'thumbnail', fatal=False)

        return {
            'id': video_id,
            'url': video_url,
            'uploader': None,
            'upload_date': None,
            'title': video_title,
            'ext': 'flv',
            'thumbnail': video_thumbnail,
            'description': None,
            'age_limit': 18,
        }
