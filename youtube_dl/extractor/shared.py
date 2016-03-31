from __future__ import unicode_literals

import base64

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    int_or_none,
    sanitized_Request,
    urlencode_postdata,
)


class SharedIE(InfoExtractor):
    IE_DESC = 'shared.sx and vivo.sx'
    _VALID_URL = r'https?://(?:shared|vivo)\.sx/(?P<id>[\da-z]{10})'

    _TESTS = [{
        'url': 'http://shared.sx/0060718775',
        'md5': '106fefed92a8a2adb8c98e6a0652f49b',
        'info_dict': {
            'id': '0060718775',
            'ext': 'mp4',
            'title': 'Bmp4',
            'filesize': 1720110,
        },
    }, {
        'url': 'http://vivo.sx/d7ddda0e78',
        'md5': '15b3af41be0b4fe01f4df075c2678b2c',
        'info_dict': {
            'id': 'd7ddda0e78',
            'ext': 'mp4',
            'title': 'Chicken',
            'filesize': 528031,
        },
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        if '>File does not exist<' in webpage:
            raise ExtractorError(
                'Video %s does not exist' % video_id, expected=True)

        download_form = self._hidden_inputs(webpage)
        request = sanitized_Request(
            url, urlencode_postdata(download_form))
        request.add_header('Content-Type', 'application/x-www-form-urlencoded')

        video_page = self._download_webpage(
            request, video_id, 'Downloading video page')

        video_url = self._html_search_regex(
            r'data-url="([^"]+)"', video_page, 'video URL')
        title = base64.b64decode(self._html_search_meta(
            'full:title', webpage, 'title').encode('utf-8')).decode('utf-8')
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
