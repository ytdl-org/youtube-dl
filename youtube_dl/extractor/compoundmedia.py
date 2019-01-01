# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor

from ..utils import (
    ExtractorError,
    urlencode_postdata,
)


class CompoundMediaIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?compoundmedia\.com/shows/[^/]+/(?P<id>[0-9]+)'
    _LOGIN_URL = 'https://www.compoundmedia.com/api/login'
    _METADATA_URL_PREFIX = 'https://www.compoundmedia.com/api/video/'
    _NETRC_MACHINE = 'compoundmedia'

    def _real_extract(self, url):
        video_id = self._match_id(url)

        username, password = self._get_login_info()
        if username is None:
            self.raise_login_required()

        data = {
            'email': username,
            'password': password,
        }

        login_page, url_handle = self._download_json_handle(
            self._LOGIN_URL, None, 'Logging in',
            data=urlencode_postdata(data), headers={
                'Content-Type': 'application/x-www-form-urlencoded',
                'Referer': self._LOGIN_URL,
            })

        if login_page.get('token') is None:
            raise ExtractorError('Invalid username or password', expected=True)

        metadata = self._download_json(
            self._METADATA_URL_PREFIX + video_id, None, 'Requesting Metadata')

        url = metadata['m3u8']
        url = url.replace(
            'https://livestreamapis.com/v3', 'https://livestream.com')

        return self.url_result(url, 'Livestream')
