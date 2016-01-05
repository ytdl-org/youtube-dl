from __future__ import unicode_literals

from .common import InfoExtractor
from ..compat import (
    compat_HTTPError,
    compat_urllib_parse,
    compat_urllib_request,
)
from ..utils import (
    ExtractorError,
    float_or_none,
    int_or_none,
    sanitized_Request,
    unescapeHTML,
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

    def _enroll_course(self, webpage, course_id):
        checkout_url = unescapeHTML(self._search_regex(
            r'href=(["\'])(?P<url>https?://(?:www\.)?udemy\.com/payment/checkout/.+?)\1',
            webpage, 'checkout url', group='url', default=None))
        if checkout_url:
            raise ExtractorError(
                'Course %s is not free. You have to pay for it before you can download. '
                'Use this URL to confirm purchase: %s' % (course_id, checkout_url), expected=True)

        enroll_url = unescapeHTML(self._search_regex(
            r'href=(["\'])(?P<url>https?://(?:www\.)?udemy\.com/course/subscribe/.+?)\1',
            webpage, 'enroll url', group='url', default=None))
        if enroll_url:
            webpage = self._download_webpage(enroll_url, course_id, 'Enrolling in the course')
            if '>You have enrolled in' in webpage:
                self.to_screen('%s: Successfully enrolled in the course' % course_id)

    def _download_lecture(self, course_id, lecture_id):
        return self._download_json(
            'https://www.udemy.com/api-2.0/users/me/subscribed-courses/%s/lectures/%s?%s' % (
                course_id, lecture_id, compat_urllib_parse.urlencode({
                    'video_only': '',
                    'auto_play': '',
                    'fields[lecture]': 'title,description,asset',
                    'fields[asset]': 'asset_type,stream_url,thumbnail_url,download_urls,data',
                    'instructorPreviewMode': 'False',
                })),
            lecture_id, 'Downloading lecture JSON')

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
                headers['X-Udemy-Authorization'] = 'Bearer %s' % cookie.value

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
            return

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

        webpage = self._download_webpage(url, lecture_id)

        course_id = self._search_regex(
            r'data-course-id=["\'](\d+)', webpage, 'course id')

        try:
            lecture = self._download_lecture(course_id, lecture_id)
        except ExtractorError as e:
            # Error could possibly mean we are not enrolled in the course
            if isinstance(e.cause, compat_HTTPError) and e.cause.code == 403:
                self._enroll_course(webpage, course_id)
                lecture = self._download_lecture(course_id, lecture_id)
            else:
                raise

        title = lecture['title']
        description = lecture.get('description')

        asset = lecture['asset']

        asset_type = asset.get('assetType') or asset.get('asset_type')
        if asset_type != 'Video':
            raise ExtractorError(
                'Lecture %s is not a video' % lecture_id, expected=True)

        stream_url = asset.get('streamUrl') or asset.get('stream_url')
        if stream_url:
            youtube_url = self._search_regex(
                r'(https?://www\.youtube\.com/watch\?v=.*)', stream_url, 'youtube URL', default=None)
            if youtube_url:
                return self.url_result(youtube_url, 'Youtube')

        video_id = asset['id']
        thumbnail = asset.get('thumbnailUrl') or asset.get('thumbnail_url')
        duration = float_or_none(asset.get('data', {}).get('duration'))
        outputs = asset.get('data', {}).get('outputs', {})

        formats = []
        for format_ in asset.get('download_urls', {}).get('Video', []):
            video_url = format_.get('file')
            if not video_url:
                continue
            format_id = format_.get('label')
            f = {
                'url': format_['file'],
                'height': int_or_none(format_id),
            }
            if format_id:
                # Some videos contain additional metadata (e.g.
                # https://www.udemy.com/ios9-swift/learn/#/lecture/3383208)
                output = outputs.get(format_id)
                if isinstance(output, dict):
                    f.update({
                        'format_id': '%sp' % (output.get('label') or format_id),
                        'width': int_or_none(output.get('width')),
                        'height': int_or_none(output.get('height')),
                        'vbr': int_or_none(output.get('video_bitrate_in_kbps')),
                        'vcodec': output.get('video_codec'),
                        'fps': int_or_none(output.get('frame_rate')),
                        'abr': int_or_none(output.get('audio_bitrate_in_kbps')),
                        'acodec': output.get('audio_codec'),
                        'asr': int_or_none(output.get('audio_sample_rate')),
                        'tbr': int_or_none(output.get('total_bitrate_in_kbps')),
                        'filesize': int_or_none(output.get('file_size_in_bytes')),
                    })
                else:
                    f['format_id'] = '%sp' % format_id
            formats.append(f)

        self._sort_formats(formats)

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
    _VALID_URL = r'https?://www\.udemy\.com/(?P<id>[\da-z-]+)'
    _TESTS = []

    @classmethod
    def suitable(cls, url):
        return False if UdemyIE.suitable(url) else super(UdemyCourseIE, cls).suitable(url)

    def _real_extract(self, url):
        course_path = self._match_id(url)

        webpage = self._download_webpage(url, course_path)

        response = self._download_json(
            'https://www.udemy.com/api-1.1/courses/%s' % course_path,
            course_path, 'Downloading course JSON')

        course_id = response['id']
        course_title = response.get('title')

        self._enroll_course(webpage, course_id)

        response = self._download_json(
            'https://www.udemy.com/api-1.1/courses/%s/curriculum' % course_id,
            course_id, 'Downloading course curriculum')

        entries = []
        chapter, chapter_number = None, None
        for asset in response:
            asset_type = asset.get('assetType') or asset.get('asset_type')
            if asset_type == 'Video':
                asset_id = asset.get('id')
                if asset_id:
                    entry = {
                        '_type': 'url_transparent',
                        'url': 'https://www.udemy.com/%s/#/lecture/%s' % (course_path, asset['id']),
                        'ie_key': UdemyIE.ie_key(),
                    }
                    if chapter_number:
                        entry['chapter_number'] = chapter_number
                    if chapter:
                        entry['chapter'] = chapter
                    entries.append(entry)
            elif asset.get('type') == 'chapter':
                chapter_number = asset.get('index') or asset.get('object_index')
                chapter = asset.get('title')

        return self.playlist_result(entries, course_id, course_title)
