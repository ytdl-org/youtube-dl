from __future__ import unicode_literals

import re
import base64

from .common import InfoExtractor
from ..compat import (
    compat_urllib_parse,
    compat_urllib_request,
)
from ..utils import (
    ExtractorError,
    int_or_none,
)


class SharedIE(InfoExtractor):
    _VALID_URL = r'http://shared\.sx/(?P<id>[\da-z]{10})'

    _TEST = {
        'url': 'http://shared.sx/0060718775',
        'md5': '106fefed92a8a2adb8c98e6a0652f49b',
        'info_dict': {
            'id': '0060718775',
            'ext': 'mp4',
            'title': 'Bmp4',
        },
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        if '>File does not exist<' in webpage:
            raise ExtractorError(
                'Video %s does not exist' % video_id, expected=True)

        download_form = dict(re.findall(
            r'<input type="hidden" name="([^"]+)" value="([^"]*)"', webpage))
        request = compat_urllib_request.Request(
            url, compat_urllib_parse.urlencode(download_form))
        request.add_header('Content-Type', 'application/x-www-form-urlencoded')

        video_page = self._download_webpage(
            request, video_id, 'Downloading video page')

        video_url = self._html_search_regex(
            r'data-url="([^"]+)"', video_page, 'video URL')
        title = base64.b64decode(self._html_search_meta(
            'full:title', webpage, 'title')).decode('utf-8')
        filesize = int_or_none(self._html_search_meta(
            'full:size', webpage, 'file size', fatal=False))
        thumbnail = self._html_search_regex(
            r'data-poster="([^"]+)"', video_page, 'thumbnail', default=None)

        return {
            'id': video_id,
            'url': video_url,
            'ext': 'mp4',
            'filesize': filesize,
            'title': title,
            'thumbnail': thumbnail,
        }
