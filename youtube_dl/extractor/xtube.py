from __future__ import unicode_literals

import os
import re

from .common import InfoExtractor
from ..utils import (
    compat_urllib_parse_urlparse,
    compat_urllib_request,
    parse_duration,
    str_to_int,
)


class XTubeIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?(?P<url>xtube\.com/watch\.php\?v=(?P<videoid>[^/?&]+))'
    _TEST = {
        'url': 'http://www.xtube.com/watch.php?v=kVTUy_G222_',
        'md5': '092fbdd3cbe292c920ef6fc6a8a9cdab',
        'info_dict': {
            'id': 'kVTUy_G222_',
            'ext': 'mp4',
            'title': 'strange erotica',
            'description': 'surreal gay themed erotica...almost an ET kind of thing',
            'uploader': 'greenshowers',
            'duration': 450,
            'age_limit': 18,
        }
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('videoid')
        url = 'http://www.' + mobj.group('url')

        req = compat_urllib_request.Request(url)
        req.add_header('Cookie', 'age_verified=1')
        webpage = self._download_webpage(req, video_id)

        video_title = self._html_search_regex(r'<p class="title">([^<]+)', webpage, 'title')
        video_uploader = self._html_search_regex(
            r'so_s\.addVariable\("owner_u", "([^"]+)', webpage, 'uploader', fatal=False)
        video_description = self._html_search_regex(
            r'<p class="fieldsDesc">([^<]+)', webpage, 'description', fatal=False)
        video_url = self._html_search_regex(r'var videoMp4 = "([^"]+)', webpage, 'video_url').replace('\\/', '/')
        duration = parse_duration(self._html_search_regex(
            r'<span class="bold">Runtime:</span> ([^<]+)</p>', webpage, 'duration', fatal=False))
        view_count = self._html_search_regex(
            r'<span class="bold">Views:</span> ([\d,\.]+)</p>', webpage, 'view count', fatal=False)
        if view_count:
            view_count = str_to_int(view_count)
        comment_count = self._html_search_regex(
            r'<div id="commentBar">([\d,\.]+) Comments</div>', webpage, 'comment count', fatal=False)
        if comment_count:
            comment_count = str_to_int(comment_count)

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
            'duration': duration,
            'view_count': view_count,
            'comment_count': comment_count,
            'url': video_url,
            'ext': extension,
            'format': format,
            'format_id': format,
            'age_limit': 18,
        }
