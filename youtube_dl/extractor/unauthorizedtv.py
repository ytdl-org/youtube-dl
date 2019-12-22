# coding: utf-8
from __future__ import unicode_literals

import json

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
)


class UnauthorizedTvIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?unauthorized\.tv/programs/.*?cid=(?P<id>\d+)'
    _LOGIN_URL = 'https://www.unauthorized.tv/api/sessions'
    _NETRC_MACHINE = 'unauthorizedtv'

    def _real_extract(self, url):

        username, password = self._get_login_info()
        if username is None:
            self.raise_login_required()

        data = {
            'email': username,
            'password': password,
        }

        login_page = self._download_json(
            self._LOGIN_URL, None, 'Logging in',
            data=json.dumps(data).encode(), headers={
                'Content-Type': 'application/json',
                'Referer': self._LOGIN_URL,
            })

        if login_page.get('id') is None:
            raise ExtractorError('Invalid username or password', expected=True)

        video_id = self._match_id(url)

        metadata = self._download_json(
            'https://www.unauthorized.tv/api/chapters?ids[]=%s' % video_id,
            video_id,
        )

        video_title = metadata[0]['title']
        video_url = metadata[0]['subject']['versions']['hls']

        return {
            'id': video_id,
            'title': video_title,
            'url': video_url,
            'ext': 'mp4',
        }
