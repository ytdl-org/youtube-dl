# coding: utf-8
from __future__ import unicode_literals

from ..utils import (
    ExtractorError,
    compat_urllib_parse,
    compat_urllib_request,
    determine_ext,
)
import re

from .common import InfoExtractor


class SockshareIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?sockshare\.com/file/(?P<id>[0-9A-Za-z]+)'
    _FILE_DELETED_REGEX = r'This file doesn\'t exist, or has been removed\.</div>'
    _TEST = {
        'url': 'http://www.sockshare.com/file/437BE28B89D799D7',
        'md5': '9d0bf1cfb6dbeaa8d562f6c97506c5bd',
        'info_dict': {
            'id': '437BE28B89D799D7',
            'title': 'big_buck_bunny_720p_surround.avi',
            'ext': 'avi',
            'thumbnail': 're:^http://.*\.jpg$',
        }
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')

        url = 'http://sockshare.com/file/%s' % video_id
        webpage = self._download_webpage(url, video_id)

        if re.search(self._FILE_DELETED_REGEX, webpage) is not None:
            raise ExtractorError('Video %s does not exist' % video_id,
                                 expected=True)

        confirm_hash = self._html_search_regex(r'''(?x)<input\s+
            type="hidden"\s+
            value="([^"]*)"\s+
            name="hash"
            ''', webpage, 'hash')

        fields = {
            "hash": confirm_hash,
            "confirm": "Continue as Free User"
        }

        post = compat_urllib_parse.urlencode(fields)
        req = compat_urllib_request.Request(url, post)
        # Apparently, this header is required for confirmation to work.
        req.add_header('Host', 'www.sockshare.com')
        req.add_header('Content-type', 'application/x-www-form-urlencoded')

        webpage = self._download_webpage(
            req, video_id, 'Downloading video page')

        video_url = self._html_search_regex(
            r'<a href="([^"]*)".+class="download_file_link"',
            webpage, 'file url')
        video_url = "http://www.sockshare.com" + video_url
        title = self._html_search_regex((
            r'<h1>(.+)<strong>',
            r'var name = "([^"]+)";'),
            webpage, 'title', default=None)
        thumbnail = self._html_search_regex(
            r'<img\s+src="([^"]*)".+?name="bg"',
            webpage, 'thumbnail')

        formats = [{
            'format_id': 'sd',
            'url': video_url,
            'ext': determine_ext(title),
        }]

        return {
            'id': video_id,
            'title': title,
            'thumbnail': thumbnail,
            'formats': formats,
        }
