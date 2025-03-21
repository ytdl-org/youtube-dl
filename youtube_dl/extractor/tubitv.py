# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..compat import compat_str
from ..utils import (
    ExtractorError,
    int_or_none,
    sanitized_Request,
    urlencode_postdata,
)


class TubiTvIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?tubitv\.com/(?:video|movies|tv-shows|live)/(?P<id>[0-9]+)'
    _LOGIN_URL = 'http://tubitv.com/login'
    _NETRC_MACHINE = 'tubitv'
    _GEO_COUNTRIES = ['US']
    _TESTS = [{
        'url': 'https://tubitv.com/movies/229877/carnival-of-souls',
        'md5': '275a9f78428cfd6428520989408bcfe9',
        'info_dict': {
            'id': '229877',
            'ext': 'mp4',
            'title': 'Carnival of Souls',
            'description': 'After a traumatic accident, a woman becomes drawn to a mysterious abandoned carnival.',
            'uploader_id': 'da2522b1c94be4a578da6ba674925159',
        },
    }, {
        'url': 'https://tubitv.com/live/715943/wb-tv-watchlist',
        'info_dict': {
            'id': '715943',
            'ext': 'mp4',
            'title': 'WB TV Watchlist',
            'description': compat_str,
            'uploader_id': 'a12923a141282c8b62e593bac425db99',
            'is_live': True,
        },
    }]

    def _login(self):
        username, password = self._get_login_info()
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
        title = video_data['title']

        formats = self._extract_m3u8_formats(
            self._proto_relative_url(traverse_obj(video_data, 'url', ('video_resources', 0, 'manifest', 'url'))),
            video_id, 'mp4', 'm3u8_native')
        self._sort_formats(formats)

        thumbnails = []
        for thumbnail_url in video_data.get('thumbnails', []):
            if not thumbnail_url:
                continue
            thumbnails.append({
                'url': self._proto_relative_url(thumbnail_url),
            })

        subtitles = {}
        for sub in video_data.get('subtitles', []):
            sub_url = sub.get('url')
            if not sub_url:
                continue
            subtitles.setdefault(sub.get('lang', 'English'), []).append({
                'url': self._proto_relative_url(sub_url),
            })

        is_live = ('live' in video_data.get('tags') or []) or None

        return {
            'id': video_id,
            'title': title,
            'formats': formats,
            'subtitles': subtitles,
            'thumbnails': thumbnails,
            'description': video_data.get('description'),
            'duration': int_or_none(video_data.get('duration')),
            'uploader_id': video_data.get('publisher_id'),
            'release_year': int_or_none(video_data.get('year')),
            'is_live': is_live,
        }
