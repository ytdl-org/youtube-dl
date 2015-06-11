from __future__ import unicode_literals

import json
import re

from .common import InfoExtractor
from ..compat import (
    compat_urllib_parse_urlparse,
    compat_urllib_request,
)
from ..utils import (
    int_or_none,
    str_to_int,
)
from ..aes import aes_decrypt_text


class Tube8IE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?tube8\.com/(?:[^/]+/)+(?P<display_id>[^/]+)/(?P<id>\d+)'
    _TESTS = [
        {
            'url': 'http://www.tube8.com/teen/kasia-music-video/229795/',
            'md5': '44bf12b98313827dd52d35b8706a4ea0',
            'info_dict': {
                'id': '229795',
                'display_id': 'kasia-music-video',
                'ext': 'mp4',
                'description': 'hot teen Kasia grinding',
                'uploader': 'unknown',
                'title': 'Kasia music video',
                'age_limit': 18,
            }
        },
        {
            'url': 'http://www.tube8.com/shemale/teen/blonde-cd-gets-kidnapped-by-two-blacks-and-punished-for-being-a-slutty-girl/19569151/',
            'only_matching': True,
        },
    ]

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')
        display_id = mobj.group('display_id')

        req = compat_urllib_request.Request(url)
        req.add_header('Cookie', 'age_verified=1')
        webpage = self._download_webpage(req, display_id)

        flashvars = json.loads(self._html_search_regex(
            r'flashvars\s*=\s*({.+?});\r?\n', webpage, 'flashvars'))

        video_url = flashvars['video_url']
        if flashvars.get('encrypted') is True:
            video_url = aes_decrypt_text(video_url, flashvars['video_title'], 32).decode('utf-8')
        path = compat_urllib_parse_urlparse(video_url).path
        format_id = '-'.join(path.split('/')[4].split('_')[:2])

        thumbnail = flashvars.get('image_url')

        title = self._html_search_regex(
            r'videoTitle\s*=\s*"([^"]+)', webpage, 'title')
        description = self._html_search_regex(
            r'>Description:</strong>\s*(.+?)\s*<', webpage, 'description', fatal=False)
        uploader = self._html_search_regex(
            r'<span class="username">\s*(.+?)\s*<',
            webpage, 'uploader', fatal=False)

        like_count = int_or_none(self._html_search_regex(
            r'rupVar\s*=\s*"(\d+)"', webpage, 'like count', fatal=False))
        dislike_count = int_or_none(self._html_search_regex(
            r'rdownVar\s*=\s*"(\d+)"', webpage, 'dislike count', fatal=False))
        view_count = self._html_search_regex(
            r'<strong>Views: </strong>([\d,\.]+)\s*</li>', webpage, 'view count', fatal=False)
        if view_count:
            view_count = str_to_int(view_count)
        comment_count = self._html_search_regex(
            r'<span id="allCommentsCount">(\d+)</span>', webpage, 'comment count', fatal=False)
        if comment_count:
            comment_count = str_to_int(comment_count)

        return {
            'id': video_id,
            'display_id': display_id,
            'url': video_url,
            'title': title,
            'description': description,
            'thumbnail': thumbnail,
            'uploader': uploader,
            'format_id': format_id,
            'view_count': view_count,
            'like_count': like_count,
            'dislike_count': dislike_count,
            'comment_count': comment_count,
            'age_limit': 18,
        }
