from __future__ import unicode_literals

import json
import random
import re

from .common import InfoExtractor
from ..compat import (
    compat_b64decode,
    compat_HTTPError,
)
from ..utils import (
    ExtractorError,
    orderedSet,
    unescapeHTML,
    urlencode_postdata,
    urljoin,
)


class LinuxAcademyIE(InfoExtractor):
    _VALID_URL = r'''(?x)
                    https?://
                        (?:www\.)?linuxacademy\.com/cp/
                        (?:
                            courses/lesson/course/(?P<chapter_id>\d+)/lesson/(?P<lesson_id>\d+)|
                            modules/view/id/(?P<course_id>\d+)
                        )
                    '''
    _TESTS = [{
        'url': 'https://linuxacademy.com/cp/courses/lesson/course/1498/lesson/2/module/154',
        'info_dict': {
            'id': '1498-2',
            'ext': 'mp4',
            'title': "Introduction to the Practitioner's Brief",
        },
        'params': {
            'skip_download': True,
        },
        'skip': 'Requires Linux Academy account credentials',
    }, {
        'url': 'https://linuxacademy.com/cp/courses/lesson/course/1498/lesson/2',
        'only_matching': True,
    }, {
        'url': 'https://linuxacademy.com/cp/modules/view/id/154',
        'info_dict': {
            'id': '154',
            'title': 'AWS Certified Cloud Practitioner',
            'description': 'md5:039db7e60e4aac9cf43630e0a75fa834',
        },
        'playlist_count': 41,
        'skip': 'Requires Linux Academy account credentials',
    }]

    _AUTHORIZE_URL = 'https://login.linuxacademy.com/authorize'
    _ORIGIN_URL = 'https://linuxacademy.com'
    _CLIENT_ID = 'KaWxNn1C2Gc7n83W9OFeXltd8Utb5vvx'
    _NETRC_MACHINE = 'linuxacademy'

    def _real_initialize(self):
        self._login()

    def _login(self):
        username, password = self._get_login_info()
        if username is None:
            return

        def random_string():
            return ''.join([
                random.choice('0123456789ABCDEFGHIJKLMNOPQRSTUVXYZabcdefghijklmnopqrstuvwxyz-._~')
                for _ in range(32)])

        webpage, urlh = self._download_webpage_handle(
            self._AUTHORIZE_URL, None, 'Downloading authorize page', query={
                'client_id': self._CLIENT_ID,
                'response_type': 'token id_token',
                'redirect_uri': self._ORIGIN_URL,
                'scope': 'openid email user_impersonation profile',
                'audience': self._ORIGIN_URL,
                'state': random_string(),
                'nonce': random_string(),
            })

        login_data = self._parse_json(
            self._search_regex(
                r'atob\(\s*(["\'])(?P<value>(?:(?!\1).)+)\1', webpage,
                'login info', group='value'), None,
            transform_source=lambda x: compat_b64decode(x).decode('utf-8')
        )['extraParams']

        login_data.update({
            'client_id': self._CLIENT_ID,
            'redirect_uri': self._ORIGIN_URL,
            'tenant': 'lacausers',
            'connection': 'Username-Password-Authentication',
            'username': username,
            'password': password,
            'sso': 'true',
        })

        login_state_url = urlh.geturl()

        try:
            login_page = self._download_webpage(
                'https://login.linuxacademy.com/usernamepassword/login', None,
                'Downloading login page', data=json.dumps(login_data).encode(),
                headers={
                    'Content-Type': 'application/json',
                    'Origin': 'https://login.linuxacademy.com',
                    'Referer': login_state_url,
                })
        except ExtractorError as e:
            if isinstance(e.cause, compat_HTTPError) and e.cause.code == 401:
                error = self._parse_json(e.cause.read(), None)
                message = error.get('description') or error['code']
                raise ExtractorError(
                    '%s said: %s' % (self.IE_NAME, message), expected=True)
            raise

        callback_page, urlh = self._download_webpage_handle(
            'https://login.linuxacademy.com/login/callback', None,
            'Downloading callback page',
            data=urlencode_postdata(self._hidden_inputs(login_page)),
            headers={
                'Content-Type': 'application/x-www-form-urlencoded',
                'Origin': 'https://login.linuxacademy.com',
                'Referer': login_state_url,
            })

        access_token = self._search_regex(
            r'access_token=([^=&]+)', urlh.geturl(),
            'access token')

        self._download_webpage(
            'https://linuxacademy.com/cp/login/tokenValidateLogin/token/%s'
            % access_token, None, 'Downloading token validation page')

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        chapter_id, lecture_id, course_id = mobj.group('chapter_id', 'lesson_id', 'course_id')
        item_id = course_id if course_id else '%s-%s' % (chapter_id, lecture_id)

        webpage = self._download_webpage(url, item_id)

        # course path
        if course_id:
            entries = [
                self.url_result(
                    urljoin(url, lesson_url), ie=LinuxAcademyIE.ie_key())
                for lesson_url in orderedSet(re.findall(
                    r'<a[^>]+\bhref=["\'](/cp/courses/lesson/course/\d+/lesson/\d+/module/\d+)',
                    webpage))]
            title = unescapeHTML(self._html_search_regex(
                (r'class=["\']course-title["\'][^>]*>(?P<value>[^<]+)',
                 r'var\s+title\s*=\s*(["\'])(?P<value>(?:(?!\1).)+)\1'),
                webpage, 'title', default=None, group='value'))
            description = unescapeHTML(self._html_search_regex(
                r'var\s+description\s*=\s*(["\'])(?P<value>(?:(?!\1).)+)\1',
                webpage, 'description', default=None, group='value'))
            return self.playlist_result(entries, course_id, title, description)

        # single video path
        info = self._extract_jwplayer_data(
            webpage, item_id, require_title=False, m3u8_id='hls',)
        title = self._search_regex(
            (r'>Lecture\s*:\s*(?P<value>[^<]+)',
             r'lessonName\s*=\s*(["\'])(?P<value>(?:(?!\1).)+)\1'), webpage,
            'title', group='value')
        info.update({
            'id': item_id,
            'title': title,
        })
        return info
