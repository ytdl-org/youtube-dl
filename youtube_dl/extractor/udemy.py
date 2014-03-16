from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    compat_urllib_parse,
    compat_urllib_request,
    ExtractorError,
)


class UdemyIE(InfoExtractor):
    IE_NAME = 'udemy'
    _VALID_URL = r'https?://www\.udemy\.com/(?:[^#]+#/lecture/|lecture/view/?\?lectureId=)(?P<id>\d+)'
    _LOGIN_URL = 'https://www.udemy.com/join/login-submit/'
    _NETRC_MACHINE = 'udemy'

    _TESTS = [{
        'url': 'https://www.udemy.com/java-tutorial/#/lecture/172757',
        'md5': '98eda5b657e752cf945d8445e261b5c5',
        'info_dict': {
            'id': '160614',
            'ext': 'mp4',
            'title': 'Introduction and Installation',
            'description': 'md5:c0d51f6f21ef4ec65f091055a5eef876',
            'duration': 579.29,
        },
        'skip': 'Requires udemy account credentials',
    }]

    def _handle_error(self, response):
        if not isinstance(response, dict):
            return
        error = response.get('error')
        if error:
            error_str = 'Udemy returned error #%s: %s' % (error.get('code'), error.get('message'))
            error_data = error.get('data')
            if error_data:
                error_str += ' - %s' % error_data.get('formErrors')
            raise ExtractorError(error_str, expected=True)

    def _download_json(self, url, video_id, note='Downloading JSON metadata'):
        response = super(UdemyIE, self)._download_json(url, video_id, note)
        self._handle_error(response)
        return response

    def _real_initialize(self):
        self._login()

    def _login(self):
        (username, password) = self._get_login_info()
        if username is None:
            raise ExtractorError(
                'Udemy account is required, use --username and --password options to provide account credentials.',
                expected=True)

        login_popup = self._download_webpage(
            'https://www.udemy.com/join/login-popup?displayType=ajax&showSkipButton=1', None,
            'Downloading login popup')

        if login_popup == '<div class="run-command close-popup redirect" data-url="https://www.udemy.com/"></div>':
            return

        csrf = self._html_search_regex(r'<input type="hidden" name="csrf" value="(.+?)"', login_popup, 'csrf token')

        login_form = {
            'email': username,
            'password': password,
            'csrf': csrf,
            'displayType': 'json',
            'isSubmitted': '1',
        }
        request = compat_urllib_request.Request(self._LOGIN_URL, compat_urllib_parse.urlencode(login_form))
        response = self._download_json(request, None, 'Logging in as %s' % username)

        if 'returnUrl' not in response:
            raise ExtractorError('Unable to log in')

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        lecture_id = mobj.group('id')

        lecture = self._download_json(
            'https://www.udemy.com/api-1.1/lectures/%s' % lecture_id, lecture_id, 'Downloading lecture JSON')

        if lecture['assetType'] != 'Video':
            raise ExtractorError('Lecture %s is not a video' % lecture_id, expected=True)

        asset = lecture['asset']

        stream_url = asset['streamUrl']
        mobj = re.search(r'(https?://www\.youtube\.com/watch\?v=.*)', stream_url)
        if mobj:
            return self.url_result(mobj.group(1), 'Youtube')

        video_id = asset['id']
        thumbnail = asset['thumbnailUrl']
        duration = asset['data']['duration']

        download_url = asset['downloadUrl']

        formats = [
            {
                'url': download_url['Video480p'][0],
                'format_id': '360p',
            },
            {
                'url': download_url['Video'][0],
                'format_id': '720p',
            },
        ]

        title = lecture['title']
        description = lecture['description']

        return {
            'id': video_id,
            'title': title,
            'description': description,
            'thumbnail': thumbnail,
            'duration': duration,
            'formats': formats
        }


class UdemyCourseIE(UdemyIE):
    IE_NAME = 'udemy:course'
    _VALID_URL = r'https?://www\.udemy\.com/(?P<coursepath>[\da-z-]+)'
    _SUCCESSFULLY_ENROLLED = '>You have enrolled in this course!<'
    _ALREADY_ENROLLED = '>You are already taking this course.<'
    _TESTS = []

    @classmethod
    def suitable(cls, url):
        return False if UdemyIE.suitable(url) else super(UdemyCourseIE, cls).suitable(url)

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        course_path = mobj.group('coursepath')

        response = self._download_json(
            'https://www.udemy.com/api-1.1/courses/%s' % course_path, course_path, 'Downloading course JSON')

        course_id = int(response['id'])
        course_title = response['title']

        webpage = self._download_webpage(
            'https://www.udemy.com/course/subscribe/?courseId=%s' % course_id, course_id, 'Enrolling in the course')

        if self._SUCCESSFULLY_ENROLLED in webpage:
            self.to_screen('%s: Successfully enrolled in' % course_id)
        elif self._ALREADY_ENROLLED in webpage:
            self.to_screen('%s: Already enrolled in' % course_id)

        response = self._download_json('https://www.udemy.com/api-1.1/courses/%s/curriculum' % course_id,
            course_id, 'Downloading course curriculum')

        entries = [
            self.url_result('https://www.udemy.com/%s/#/lecture/%s' % (course_path, asset['id']), 'Udemy')
            for asset in response if asset.get('assetType') == 'Video'
        ]

        return self.playlist_result(entries, course_id, course_title)