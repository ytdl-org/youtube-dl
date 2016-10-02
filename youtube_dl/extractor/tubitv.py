# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    int_or_none,
    sanitized_Request,
    urlencode_postdata,
    parse_iso8601,
)


class TubiTvIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?tubitv\.com/video/(?P<id>[0-9]+)'
    _LOGIN_URL = 'http://tubitv.com/login'
    _NETRC_MACHINE = 'tubitv'
    _TEST = {
        'url': 'http://tubitv.com/video/283829/the_comedian_at_the_friday',
        'info_dict': {
            'id': '283829',
            'ext': 'mp4',
            'title': 'The Comedian at The Friday',
            'description': 'A stand up comedian is forced to look at the decisions in his life while on a one week trip to the west coast.',
            'uploader': 'Indie Rights Films',
            'upload_date': '20160111',
            'timestamp': 1452555979,
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
        payload = urlencode_postdata(form_data)
        request = sanitized_Request(self._LOGIN_URL, payload)
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
        video_data = self._download_json(
            'http://tubitv.com/oz/videos/%s/content' % video_id, video_id)
        title = video_data['n']

        formats = self._extract_m3u8_formats(
            video_data['mh'], video_id, 'mp4', 'm3u8_native')
        self._sort_formats(formats)

        subtitles = {}
        for sub in video_data.get('sb', []):
            sub_url = sub.get('u')
            if not sub_url:
                continue
            subtitles.setdefault(sub.get('l', 'en'), []).append({
                'url': sub_url,
            })

        return {
            'id': video_id,
            'title': title,
            'formats': formats,
            'subtitles': subtitles,
            'thumbnail': video_data.get('ph'),
            'description': video_data.get('d'),
            'duration': int_or_none(video_data.get('s')),
            'timestamp': parse_iso8601(video_data.get('u')),
            'uploader': video_data.get('on'),
        }
