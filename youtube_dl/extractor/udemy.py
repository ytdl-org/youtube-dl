from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..compat import (
    compat_urllib_parse,
    compat_urllib_request,
)
from ..utils import (
    ExtractorError,
    sanitized_Request,
)


class UdemyIE(InfoExtractor):
    IE_NAME = 'udemy'
    _VALID_URL = r'https?://www\.udemy\.com/(?:[^#]+#/lecture/|lecture/view/?\?lectureId=)(?P<id>\d+)'
    _LOGIN_URL = 'https://www.udemy.com/join/login-popup/?displayType=ajax&showSkipButton=1'
    _ORIGIN_URL = 'https://www.udemy.com'
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

    def _download_json(self, url_or_request, video_id, note='Downloading JSON metadata'):
        headers = {
            'X-Udemy-Snail-Case': 'true',
            'X-Requested-With': 'XMLHttpRequest',
        }
        for cookie in self._downloader.cookiejar:
            if cookie.name == 'client_id':
                headers['X-Udemy-Client-Id'] = cookie.value
            elif cookie.name == 'access_token':
                headers['X-Udemy-Bearer-Token'] = cookie.value

        if isinstance(url_or_request, compat_urllib_request.Request):
            for header, value in headers.items():
                url_or_request.add_header(header, value)
        else:
            url_or_request = sanitized_Request(url_or_request, headers=headers)

        response = super(UdemyIE, self)._download_json(url_or_request, video_id, note)
        self._handle_error(response)
        return response

    def _real_initialize(self):
        self._login()

    def _login(self):
        (username, password) = self._get_login_info()
        if username is None:
            self.raise_login_required('Udemy account is required')

        login_popup = self._download_webpage(
            self._LOGIN_URL, None, 'Downloading login popup')

        def is_logged(webpage):
            return any(p in webpage for p in ['href="https://www.udemy.com/user/logout/', '>Logout<'])

        # already logged in
        if is_logged(login_popup):
            return

        login_form = self._form_hidden_inputs('login-form', login_popup)

        login_form.update({
            'email': username.encode('utf-8'),
            'password': password.encode('utf-8'),
        })

        request = sanitized_Request(
            self._LOGIN_URL, compat_urllib_parse.urlencode(login_form).encode('utf-8'))
        request.add_header('Referer', self._ORIGIN_URL)
        request.add_header('Origin', self._ORIGIN_URL)

        response = self._download_webpage(
            request, None, 'Logging in as %s' % username)

        if not is_logged(response):
            error = self._html_search_regex(
                r'(?s)<div[^>]+class="form-errors[^"]*">(.+?)</div>',
                response, 'error message', default=None)
            if error:
                raise ExtractorError('Unable to login: %s' % error, expected=True)
            raise ExtractorError('Unable to log in')

    def _real_extract(self, url):
        lecture_id = self._match_id(url)

        lecture = self._download_json(
            'https://www.udemy.com/api-1.1/lectures/%s' % lecture_id,
            lecture_id, 'Downloading lecture JSON')

        asset_type = lecture.get('assetType') or lecture.get('asset_type')
        if asset_type != 'Video':
            raise ExtractorError(
                'Lecture %s is not a video' % lecture_id, expected=True)

        asset = lecture['asset']

        stream_url = asset.get('streamUrl') or asset.get('stream_url')
        mobj = re.search(r'(https?://www\.youtube\.com/watch\?v=.*)', stream_url)
        if mobj:
            return self.url_result(mobj.group(1), 'Youtube')

        video_id = asset['id']
        thumbnail = asset.get('thumbnailUrl') or asset.get('thumbnail_url')
        duration = asset['data']['duration']

        download_url = asset.get('downloadUrl') or asset.get('download_url')

        video = download_url.get('Video') or download_url.get('video')
        video_480p = download_url.get('Video480p') or download_url.get('video_480p')

        formats = [
            {
                'url': video_480p[0],
                'format_id': '360p',
            },
            {
                'url': video[0],
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
            'https://www.udemy.com/api-1.1/courses/%s' % course_path,
            course_path, 'Downloading course JSON')

        course_id = int(response['id'])
        course_title = response['title']

        webpage = self._download_webpage(
            'https://www.udemy.com/course/subscribe/?courseId=%s' % course_id,
            course_id, 'Enrolling in the course')

        if self._SUCCESSFULLY_ENROLLED in webpage:
            self.to_screen('%s: Successfully enrolled in' % course_id)
        elif self._ALREADY_ENROLLED in webpage:
            self.to_screen('%s: Already enrolled in' % course_id)

        response = self._download_json(
            'https://www.udemy.com/api-1.1/courses/%s/curriculum' % course_id,
            course_id, 'Downloading course curriculum')

        entries = [
            self.url_result(
                'https://www.udemy.com/%s/#/lecture/%s' % (course_path, asset['id']), 'Udemy')
            for asset in response if asset.get('assetType') or asset.get('asset_type') == 'Video'
        ]

        return self.playlist_result(entries, course_id, course_title)
