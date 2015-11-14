# encoding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from .brightcove import BrightcoveLegacyIE

from ..compat import (
    compat_urllib_parse,
    compat_urllib_request,
)
from ..utils import (
    ExtractorError,
    smuggle_url,
    std_headers,
)


class SafariBaseIE(InfoExtractor):
    _LOGIN_URL = 'https://www.safaribooksonline.com/accounts/login/'
    _SUCCESSFUL_LOGIN_REGEX = r'<a href="/accounts/logout/"[^>]*>Sign Out</a>'
    _NETRC_MACHINE = 'safari'

    _API_BASE = 'https://www.safaribooksonline.com/api/v1/book'
    _API_FORMAT = 'json'

    LOGGED_IN = False

    def _real_initialize(self):
        # We only need to log in once for courses or individual videos
        if not self.LOGGED_IN:
            self._login()
            SafariBaseIE.LOGGED_IN = True

    def _login(self):
        (username, password) = self._get_login_info()
        if username is None:
            self.raise_login_required('safaribooksonline.com account is required')

        headers = std_headers
        if 'Referer' not in headers:
            headers['Referer'] = self._LOGIN_URL

        login_page = self._download_webpage(
            self._LOGIN_URL, None,
            'Downloading login form')

        csrf = self._html_search_regex(
            r"name='csrfmiddlewaretoken'\s+value='([^']+)'",
            login_page, 'csrf token')

        login_form = {
            'csrfmiddlewaretoken': csrf,
            'email': username,
            'password1': password,
            'login': 'Sign In',
            'next': '',
        }

        request = compat_urllib_request.Request(
            self._LOGIN_URL, compat_urllib_parse.urlencode(login_form), headers=headers)
        login_page = self._download_webpage(
            request, None, 'Logging in as %s' % username)

        if re.search(self._SUCCESSFUL_LOGIN_REGEX, login_page) is None:
            raise ExtractorError(
                'Login failed; make sure your credentials are correct and try again.',
                expected=True)

        self.to_screen('Login successful')


class SafariIE(SafariBaseIE):
    IE_NAME = 'safari'
    IE_DESC = 'safaribooksonline.com online video'
    _VALID_URL = r'''(?x)https?://
                            (?:www\.)?safaribooksonline\.com/
                                (?:
                                    library/view/[^/]+|
                                    api/v1/book
                                )/
                                (?P<course_id>[^/]+)/
                                    (?:chapter(?:-content)?/)?
                                (?P<part>part\d+)\.html
    '''

    _TESTS = [{
        'url': 'https://www.safaribooksonline.com/library/view/hadoop-fundamentals-livelessons/9780133392838/part00.html',
        'md5': '5b0c4cc1b3c1ba15dda7344085aa5592',
        'info_dict': {
            'id': '2842601850001',
            'ext': 'mp4',
            'title': 'Introduction',
        },
        'skip': 'Requires safaribooksonline account credentials',
    }, {
        'url': 'https://www.safaribooksonline.com/api/v1/book/9780133392838/chapter/part00.html',
        'only_matching': True,
    }, {
        # non-digits in course id
        'url': 'https://www.safaribooksonline.com/library/view/create-a-nodejs/100000006A0210/part00.html',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        course_id = mobj.group('course_id')
        part = mobj.group('part')

        webpage = self._download_webpage(
            '%s/%s/chapter-content/%s.html' % (self._API_BASE, course_id, part),
            part)

        bc_url = BrightcoveLegacyIE._extract_brightcove_url(webpage)
        if not bc_url:
            raise ExtractorError('Could not extract Brightcove URL from %s' % url, expected=True)

        return self.url_result(smuggle_url(bc_url, {'Referer': url}), 'BrightcoveLegacy')


class SafariCourseIE(SafariBaseIE):
    IE_NAME = 'safari:course'
    IE_DESC = 'safaribooksonline.com online courses'

    _VALID_URL = r'https?://(?:www\.)?safaribooksonline\.com/(?:library/view/[^/]+|api/v1/book)/(?P<id>[^/]+)/?(?:[#?]|$)'

    _TESTS = [{
        'url': 'https://www.safaribooksonline.com/library/view/hadoop-fundamentals-livelessons/9780133392838/',
        'info_dict': {
            'id': '9780133392838',
            'title': 'Hadoop Fundamentals LiveLessons',
        },
        'playlist_count': 22,
        'skip': 'Requires safaribooksonline account credentials',
    }, {
        'url': 'https://www.safaribooksonline.com/api/v1/book/9781449396459/?override_format=json',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        course_id = self._match_id(url)

        course_json = self._download_json(
            '%s/%s/?override_format=%s' % (self._API_BASE, course_id, self._API_FORMAT),
            course_id, 'Downloading course JSON')

        if 'chapters' not in course_json:
            raise ExtractorError(
                'No chapters found for course %s' % course_id, expected=True)

        entries = [
            self.url_result(chapter, 'Safari')
            for chapter in course_json['chapters']]

        course_title = course_json['title']

        return self.playlist_result(entries, course_id, course_title)
