# coding: utf-8
from __future__ import unicode_literals

from ..compat import (
    compat_str,
    compat_urllib_parse_urlencode
)

from .common import InfoExtractor

import re


class VeepsIE(InfoExtractor):
    _VALID_URL = r'https?://(?P<channel>[a-zA-Z0-9]+)\.veeps\.com/stream/(?P<id>[0-9a-f]+)'
    _CSRF_TOKEN_RE = InfoExtractor._meta_regex('csrf-token')
    _M3U8_RE = r'<div[^>]+data-react-props=(?:\'|")[^>\'"]*stored_stream_asset&quot;:&quot;(?P<url>[^&>\'"]+)&quot;[^>\'"]*(?:\'|")[^>]*>'

    @classmethod
    def _match_channel(cls, url):
        if '_VALID_URL_RE' not in cls.__dict__:
            cls._VALID_URL_RE = re.compile(cls._VALID_URL)
        m = cls._VALID_URL_RE.match(url)
        assert m
        return compat_str(m.group('channel'))

    def _real_initialize(self):
        if self._downloader is None:
            return
        self._login()

    def _login(self):
        first_login = self._download_webpage(
            'https://veeps.com/users/login',
            None,
            note='obtaining initial session',
            errnote='failed to obtain initial session'
        )

        authenticity_token = re.search(self._CSRF_TOKEN_RE, first_login).group('content')
        assert authenticity_token is not None

        username, password = self._get_login_info()
        assert username is not None
        assert password is not None

        post_data = compat_urllib_parse_urlencode({
            'authenticity_token': authenticity_token,
            'user[email]': username,
            'user[password]': password,
            'commit': 'Sign+In'
        }).encode('utf-8')

        self._download_webpage(
            'https://veeps.com/users/login',
            None,
            note='logging in',
            errnote='failed to login',
            data=post_data
        )

    def _real_extract(self, url):
        video_id = self._match_id(url)
        channel = self._match_channel(url)

        stream_page = self._download_webpage(
            url,
            video_id,
            note='downloading stream page',
            errnote='failed to download stream page'
        )

        m3u8_location = re.search(self._M3U8_RE, stream_page).group('url')

        return {
            'id': video_id,
            'title': '{} stream - {}'.format(channel, video_id),
            'formats': self._extract_m3u8_formats(m3u8_location, video_id, ext='mp4')
        }
