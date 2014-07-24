from __future__ import unicode_literals

import re
import base64

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    compat_urllib_request,
    compat_urllib_parse,
    int_or_none,
)


class SharedIE(InfoExtractor):
    _VALID_URL = r'http://shared\.sx/(?P<id>[\da-z]{10})'

    _TEST = {
        'url': 'http://shared.sx/0060718775',
        'md5': '53e1c58fc3e777ae1dfe9e57ba2f9c72',
        'info_dict': {
            'id': '0060718775',
            'ext': 'mp4',
            'title': 'Big Buck Bunny Trailer',
        },
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')

        page = self._download_webpage(url, video_id)

        if re.search(r'>File does not exist<', page) is not None:
            raise ExtractorError('Video %s does not exist' % video_id, expected=True)

        download_form = dict(re.findall(r'<input type="hidden" name="([^"]+)" value="([^"]*)"', page))

        request = compat_urllib_request.Request(url, compat_urllib_parse.urlencode(download_form))
        request.add_header('Content-Type', 'application/x-www-form-urlencoded')

        video_page = self._download_webpage(request, video_id, 'Downloading video page')

        video_url = self._html_search_regex(r'data-url="([^"]+)"', video_page, 'video URL')
        title = base64.b64decode(self._html_search_meta('full:title', page, 'title')).decode('utf-8')
        filesize = int_or_none(self._html_search_meta('full:size', page, 'file size', fatal=False))
        thumbnail = self._html_search_regex(
            r'data-poster="([^"]+)"', video_page, 'thumbnail', fatal=False, default=None)

        return {
            'id': video_id,
            'url': video_url,
            'ext': 'mp4',
            'filesize': filesize,
            'title': title,
            'thumbnail': thumbnail,
        }