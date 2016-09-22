# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..compat import (
    compat_urllib_parse,
    compat_urllib_parse,
    compat_urllib_parse_unquote,
    compat_urllib_request,
    compat_urlparse,
)

class HooFootIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?hoofoot\.com/(.*)'
    _TEST = {
        'url': 'http://hoofoot.com/?match=Real_Madrid_1_-_1_Villarreal_2016_09_21',
        'info_dict': {
            'id': 'IcQz',
            'ext': 'mp4',
            'title': 'extended rm',
            'description': None,
            'thumbnail': 'https://d1wst0behutosd.cloudfront.net/videos/10759353/thumb.jpg?v2r1474489699',
            'timestamp': 1474489688,
            'age_limit': 0,
            'duration': 918.33,
            'view_count': int,
            'like_count': int,
            'comment_count': int,
            'upload_date': '20160921',
        },
    }




    def _real_extract(self, url):
        # # video_id = self._match_id(url)
        parsed = compat_urllib_parse.urlparse(url)
        match = compat_urllib_parse.parse_qs(parsed.query)['match']
        video_id = ""
        if(len(match) > 0):
            video_id = match[0]
        webpage = self._download_webpage(url, video_id)
        video_url = self._search_regex(
        r'<iframe src="([^"]+)"', webpage, 'video')
        print(video_url)
        return self.url_result(video_url)