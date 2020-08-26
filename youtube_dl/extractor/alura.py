# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor

from ..compat import (
    compat_str,
    compat_urlparse,
)

from ..utils import (
    dict_get,
    ExtractorError,
    float_or_none,
    int_or_none,
    parse_duration,
    qualities,
    srt_subtitles_timecode,
    try_get,
    update_url_query,
    urlencode_postdata,
)


class AluraIE(InfoExtractor):
    _VALID_URL = r'https?://(?:cursos\.)?alura\.com\.br/course/(?P<course_name>[^/]+)/task/(?P<id>\d+)'
    _LOGIN_URL = 'https://cursos.alura.com.br/loginForm?urlAfterLogin=/loginForm'
    _VIDEO_URL = 'https://cursos.alura.com.br/course/%s/task/%s/video'
    _TEST = {
        'url': 'https://cursos.alura.com.br/course/design-patterns-python/task/9651',
        'md5': 'TODO: md5 sum of the first 10241 bytes of the video file (use --test)',
        'info_dict': {
            'id': '9651',
            'ext': 'mp4',
            'title': 'Video title goes here',
            'thumbnail': r're:^https?://.*\.jpg$',
            # TODO more properties, either as:
        }
    }

    def _real_extract(self, url):

        video_id = self._match_id(url)
        course = self._search_regex(self._VALID_URL, url, 'post url', group='course_name')
        video_url = self._VIDEO_URL % (course,video_id)

        video_dict = self._download_json(video_url, None, 'Searching for videos', expected_status=[404,500])

        if video_dict:
            webpage = self._download_webpage(url, video_id)
            video_title = self._search_regex(
                r'<span[^>]+class=(["\'])task-body-header-title-text\1[^>]*>(?P<title>[^<]+)',
                webpage, 'title', group='title')

            formats = []
            for video_obj in video_dict:
                video_url_m3u8 = video_obj.get('link')
                video_format = self._extract_m3u8_formats(
                    video_url_m3u8, None, 'mp4', entry_protocol='m3u8_native',
                    m3u8_id='hls', fatal=False)

                formats.extend(video_format)

            return {
                'id': video_id,
                'title': video_title,
                "formats": formats
            }

    def extract_output_format(src):
        return {
            'url': src.get('link'),
            'manifest_url': src.get('linkWebm'),
            'format': src.get('quality')
        }

    def _real_initialize(self):
        self._login()

    def _login(self):
        username, password = self._get_login_info()
        if username is None:
            return
        pass

        login_page = self._download_webpage(
            self._LOGIN_URL, None, 'Downloading login popup')

        def is_logged(webpage):
            return any(re.search(p, webpage) for p in (
                r'href=[\"|\']?/signout[\"|\']',
                r'>Logout<'))

        # already logged in
        if is_logged(login_page):
            return

        login_form = self._hidden_inputs(login_page)

        login_form.update({
            'username': username,
            'password': password,
        })

        post_url = self._search_regex(
            r'<form[^>]+class=["|\']signin-form["|\'] action=["|\'](?P<url>.+?)["|\']', login_page,
            'post url', default=self._LOGIN_URL, group='url')

        if not post_url.startswith('http'):
            post_url = compat_urlparse.urljoin(self._LOGIN_URL, post_url)

        self._download_webpage(
            post_url, None, 'Logging in',
            data=urlencode_postdata(login_form),
            headers={'Content-Type': 'application/x-www-form-urlencoded'})


