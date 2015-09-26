# coding: utf-8
from __future__ import unicode_literals

import codecs
import re

from .common import InfoExtractor
from ..compat import (
    compat_urllib_parse,
    compat_urllib_request
)
from ..utils import (
    ExtractorError,
    int_or_none,
)


class TubiTvIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?tubitv\.com/video\?id=(?P<id>[0-9]+)'
    _LOGIN_URL = 'http://tubitv.com/login'
    _NETRC_MACHINE = 'tubitv'
    _TEST = {
        'url': 'http://tubitv.com/video?id=54411&title=The_Kitchen_Musical_-_EP01',
        'info_dict': {
            'id': '54411',
            'ext': 'mp4',
            'title': 'The Kitchen Musical - EP01',
            'thumbnail': 're:^https?://.*\.png$',
            'description': 'md5:37532716166069b353e8866e71fefae7',
            'duration': 2407,
        },
        'params': {
            'skip_download': 'HLS download',
        },
    }

    def _login(self):
        (username, password) = self._get_login_info()
        if username is None:
            return
        self.report_login()
        form_data = {
            'username': username,
            'password': password,
        }
        payload = compat_urllib_parse.urlencode(form_data).encode('utf-8')
        request = compat_urllib_request.Request(self._LOGIN_URL, payload)
        request.add_header('Content-Type', 'application/x-www-form-urlencoded')
        login_page = self._download_webpage(
            request, None, False, 'Wrong login info')
        if not re.search(r'id="tubi-logout"', login_page):
            raise ExtractorError(
                'Login failed (invalid username/password)', expected=True)

    def _real_initialize(self):
        self._login()

    def _real_extract(self, url):
        video_id = self._match_id(url)

        webpage = self._download_webpage(url, video_id)
        if re.search(r"<(?:DIV|div) class='login-required-screen'>", webpage):
            self.raise_login_required('This video requires login')

        title = self._og_search_title(webpage)
        description = self._og_search_description(webpage)
        thumbnail = self._og_search_thumbnail(webpage)
        duration = int_or_none(self._html_search_meta(
            'video:duration', webpage, 'duration'))

        apu = self._search_regex(r"apu='([^']+)'", webpage, 'apu')
        m3u8_url = codecs.decode(apu, 'rot_13')[::-1]
        formats = self._extract_m3u8_formats(m3u8_url, video_id, ext='mp4')

        return {
            'id': video_id,
            'title': title,
            'formats': formats,
            'thumbnail': thumbnail,
            'description': description,
            'duration': duration,
        }
