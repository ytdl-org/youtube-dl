from __future__ import unicode_literals

import os
import re

from .common import InfoExtractor
from ..utils import (
    compat_urllib_parse_urlparse,
    compat_urllib_request,
)

class XTubeIE(InfoExtractor):
    _VALID_URL = r'^(?:https?://)?(?:www\.)?(?P<url>xtube\.com/watch\.php\?v=(?P<videoid>[^/?&]+))'
    _TEST = {
        'url': 'http://www.xtube.com/watch.php?v=kVTUy_G222_',
        'file': 'kVTUy_G222_.mp4',
        'md5': '092fbdd3cbe292c920ef6fc6a8a9cdab',
        'info_dict': {
            "title": "strange erotica",
            "description": "surreal gay themed erotica...almost an ET kind of thing",
            "uploader": "greenshowers",
            "age_limit": 18,
        }
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('videoid')
        url = 'http://www.' + mobj.group('url')

        req = compat_urllib_request.Request(url)
        req.add_header('Cookie', 'age_verified=1')
        webpage = self._download_webpage(req, video_id)

        video_title = self._html_search_regex(r'<div class="p_5px[^>]*>([^<]+)', webpage, 'title')
        video_uploader = self._html_search_regex(r'so_s\.addVariable\("owner_u", "([^"]+)', webpage, 'uploader', fatal=False)
        video_description = self._html_search_regex(r'<p class="video_description">([^<]+)', webpage, 'description', fatal=False)
        video_url= self._html_search_regex(r'var videoMp4 = "([^"]+)', webpage, 'video_url').replace('\\/', '/')
        path = compat_urllib_parse_urlparse(video_url).path
        extension = os.path.splitext(path)[1][1:]
        format = path.split('/')[5].split('_')[:2]
        format[0] += 'p'
        format[1] += 'k'
        format = "-".join(format)

        return {
            'id': video_id,
            'title': video_title,
            'uploader': video_uploader,
            'description': video_description,
            'url': video_url,
            'ext': extension,
            'format': format,
            'format_id': format,
            'age_limit': 18,
        }
