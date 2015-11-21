from __future__ import unicode_literals

import os
import re

from .common import InfoExtractor
from ..compat import (
    compat_urllib_parse_unquote,
    compat_urllib_parse_urlparse,
)
from ..utils import sanitized_Request


class MofosexIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?(?P<url>mofosex\.com/videos/(?P<id>[0-9]+)/.*?\.html)'
    _TEST = {
        'url': 'http://www.mofosex.com/videos/5018/japanese-teen-music-video.html',
        'md5': '1b2eb47ac33cc75d4a80e3026b613c5a',
        'info_dict': {
            'id': '5018',
            'ext': 'mp4',
            'title': 'Japanese Teen Music Video',
            'age_limit': 18,
        }
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')
        url = 'http://www.' + mobj.group('url')

        req = sanitized_Request(url)
        req.add_header('Cookie', 'age_verified=1')
        webpage = self._download_webpage(req, video_id)

        video_title = self._html_search_regex(r'<h1>(.+?)<', webpage, 'title')
        video_url = compat_urllib_parse_unquote(self._html_search_regex(r'flashvars.video_url = \'([^\']+)', webpage, 'video_url'))
        path = compat_urllib_parse_urlparse(video_url).path
        extension = os.path.splitext(path)[1][1:]
        format = path.split('/')[5].split('_')[:2]
        format = "-".join(format)

        age_limit = self._rta_search(webpage)

        return {
            'id': video_id,
            'title': video_title,
            'url': video_url,
            'ext': extension,
            'format': format,
            'format_id': format,
            'age_limit': age_limit,
        }
