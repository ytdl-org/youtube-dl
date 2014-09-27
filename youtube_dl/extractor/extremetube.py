from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    compat_urllib_parse_urlparse,
    compat_urllib_request,
    compat_urllib_parse,
    str_to_int,
)


class ExtremeTubeIE(InfoExtractor):
    _VALID_URL = r'^(?:https?://)?(?:www\.)?(?P<url>extremetube\.com/.*?video/.+?(?P<videoid>[0-9]+))(?:[/?&]|$)'
    _TESTS = [{
        'url': 'http://www.extremetube.com/video/music-video-14-british-euro-brit-european-cumshots-swallow-652431',
        'md5': '1fb9228f5e3332ec8c057d6ac36f33e0',
        'info_dict': {
            'id': '652431',
            'ext': 'mp4',
            'title': 'Music Video 14 british euro brit european cumshots swallow',
            'uploader': 'unknown',
            'view_count': int,
            'age_limit': 18,
        }
    }, {
        'url': 'http://www.extremetube.com/gay/video/abcde-1234',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('videoid')
        url = 'http://www.' + mobj.group('url')

        req = compat_urllib_request.Request(url)
        req.add_header('Cookie', 'age_verified=1')
        webpage = self._download_webpage(req, video_id)

        video_title = self._html_search_regex(
            r'<h1 [^>]*?title="([^"]+)"[^>]*>', webpage, 'title')
        uploader = self._html_search_regex(
            r'Uploaded by:\s*</strong>\s*(.+?)\s*</div>',
            webpage, 'uploader', fatal=False)
        view_count = str_to_int(self._html_search_regex(
            r'Views:\s*</strong>\s*<span>([\d,\.]+)</span>',
            webpage, 'view count', fatal=False))

        video_url = compat_urllib_parse.unquote(self._html_search_regex(
            r'video_url=(.+?)&amp;', webpage, 'video_url'))
        path = compat_urllib_parse_urlparse(video_url).path
        format = path.split('/')[5].split('_')[:2]
        format = "-".join(format)

        return {
            'id': video_id,
            'title': video_title,
            'uploader': uploader,
            'view_count': view_count,
            'url': video_url,
            'format': format,
            'format_id': format,
            'age_limit': 18,
        }
