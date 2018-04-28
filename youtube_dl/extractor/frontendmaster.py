# coding: utf-8
from __future__ import unicode_literals

import sys

import re

from youtube_dl.utils import try_get
from .common import InfoExtractor
from ..compat import (
    # compat_str,
    compat_urlparse,
    compat_str)

from ..utils import (
    ExtractorError,
    urlencode_postdata
)


class FrontEndMasterBaseIE(InfoExtractor):
    _API_BASE = 'https://api.frontendmasters.com/v1/kabuki/courses'
    _COOKIES_BASE = 'https://api.frontendmasters.com'

    _supported_resolutions = {
        'low': 360,
        'mid': 720,
        'high': 1080
    }

    _supported_formats = ['mp4', 'webm']

    def _match_course_id(self, url):
        if '_VALID_URL_RE' not in self.__dict__:
            self._VALID_URL_RE = re.compile(self._VALID_URL)
        m = self._VALID_URL_RE.match(url)
        assert m
        return compat_str(m.group('courseid'))

    def _download_course(self, course_id, url, display_id):
        response = self._download_json(
            '%s/%s' % (self._API_BASE, course_id), course_id,
            'Downloading course JSON',
            headers={
                'Content-Type': 'application/json;charset=utf-8',
                'Referer': url,
            })
        return response


class FrontEndMasterIE(FrontEndMasterBaseIE):
    IE_NAME = 'frontend-masters'
    _VALID_URL = r'https?://(?:www\.)?frontendmasters\.com/courses/(?P<courseid>[a-z\-]+)/(?P<id>[a-z\-]+)/?'
    _LOGIN_URL = 'https://frontendmasters.com/login/'
    _NETRC_MACHINE = 'frontend-masters'
    _TEST = {
        'url': 'https://frontendmasters.com/courses/content-strategy/introduction/',
        # 'md5': 'TODO: md5 sum of the first 10241 bytes of the video file (use --test)',
        'info_dict': {
            'id': 'introduction',
            'courseid': 'content-strategy',
            'ext': 'mp4',
            'title': 'Introduction'
        }
    }

    def _real_initialize(self):
        self._login()

    def _login(self):
        (username, password) = self._get_login_info()
        if username is None:
            return

        login_page = self._download_webpage(
            self._LOGIN_URL, None, 'Downloading login page')

        login_form = self._hidden_inputs(login_page)

        login_form.update({
            "username": username,
            "password": password
        })

        post_url = self._search_regex(
            r'<form[^>]+action=(["\'])(?P<url>.+?)\1', login_page,
            'post_url', default=self._LOGIN_URL, group='url')

        if not post_url.startswith('http'):
            post_url = compat_urlparse.urljoin(self._LOGIN_URL, post_url)

        response = self._download_webpage(
            post_url, None, 'Logging in',
            data=urlencode_postdata(login_form),
            headers={'Content-Type': 'application/x-www-form-urlencoded'}
        )

        logout_link = self._search_regex('(Logout .*)', response, 'logout-link')
        if not logout_link:
            raise ExtractorError('Unable to login', expected=True)

    def _real_extract(self, url):
        video_id = self._match_id(url)
        course_id = self._match_course_id(url)
        json_content = self._download_course(course_id=course_id, url=url, display_id=None)

        # TODO more code goes here, for example ...
        lesson_index = json_content['lessonSlugs'].index(video_id)
        lesson_hash = json_content['lessonHashes'][lesson_index]
        lesson_data = json_content['lessonData'][lesson_hash]
        lesson_source_base = lesson_data['sourceBase']

        cookies = self._get_cookies(self._COOKIES_BASE)
        cookies_str = ";".join(["%s=%s" % (cookie.key, cookie.value) for cookie in cookies.values()])
        video_request_url = "%s/source"
        video_request_params = {
            'r': 720,
            'f': 'mp4'
        }
        video_request_headers = {
            "origin": "https://frontendmasters.com",
            "referer": lesson_source_base,
            "cookie": cookies_str,
            'user-agent': "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/66.0.3359.117 Safari/537.36"
        }

        video_response = self._download_json(video_request_url % lesson_source_base, video_id, query=video_request_params, headers=video_request_headers)

        title = lesson_data['title']
        description = json_content['description']
        video_url = video_response['url']

        return {
            'id': video_id,
            'title': title,
            'courseid': course_id,
            'url': video_url

            # TODO more properties (see youtube_dl/extractor/common.py)
        }
