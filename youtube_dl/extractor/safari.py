# encoding: utf-8
from __future__ import unicode_literals

import re
import json

from .common import InfoExtractor
from .brightcove import BrightcoveIE

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
    _SUCCESSFUL_LOGIN_REGEX = r'<a href="/accounts/logout/"[^>]+>Sign Out</a>'
    _ACCOUNT_CREDENTIALS_HINT = ('Use --username and --password options to '
                                 'supply credentials for safaribooksonline.com ')
    _NETRC_MACHINE = 'safaribooksonline'

    LOGGED_IN = False

    def _real_initialize(self):
        # We only need to log in once for courses or individual videos
        if not SafariBaseIE.LOGGED_IN:
            self._login()
            SafariBaseIE.LOGGED_IN = True

    def _login(self):
        (username, password) = self._get_login_info()
        if username is None:
            raise ExtractorError(
                self._ACCOUNT_CREDENTIALS_HINT,
                expected=True)

        headers = std_headers
        if 'Referer' not in headers:
            headers['Referer'] = self._LOGIN_URL

        login_page = self._download_webpage(
            self._LOGIN_URL, None,
            'Downloading login form')

        csrf = self._html_search_regex(
            r"<input +type='hidden' +name='csrfmiddlewaretoken' +value='([^']+)' +/>",
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
            raise ExtractorError('Login failed; make sure your credentials are correct and '
                                 'try again.', expected=True)

        self.to_screen('Login successful')


class SafariIE(SafariBaseIE):
    IE_NAME = 'safari'
    IE_DESC = 'safaribooksonline.com online video'
    _VALID_URL = (r'https?://(?:www\.)?safaribooksonline\.com/library/view/[^/]+/'
                  '(?P<id>\d+)/(?P<part>part\d+)\.html')
    _TEST = {
        'url': ('https://www.safaribooksonline.com/library/view/'
                'hadoop-fundamentals-livelessons/9780133392838/part00.html'),
        'md5': '5b0c4cc1b3c1ba15dda7344085aa5592',
        'info_dict': {
            'id': '9780133392838',
            'ext': 'mp4',
            'title': 'Introduction',
        }
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        part = mobj.group('part')

        webpage = self._download_webpage(url, part)
        bc_url = BrightcoveIE._extract_brightcove_url(webpage)
        if not bc_url:
            raise ExtractorError('Could not extract Brightcove URL from %s' % url, expected=True)

        return {
            '_type': 'url',
            'url': smuggle_url(bc_url, {'Referer': url}),
            'ie_key': 'Brightcove'
        }


class SafariCourseIE(SafariBaseIE):
    IE_NAME = 'safari:course'
    IE_DESC = 'safaribooksonline.com online courses'

    _VALID_URL = (r'https?://(?:www\.)?safaribooksonline\.com/library/view/'
                  '(?P<course_path>[^/]+)/(?P<id>\d+)/?$')

    _API_BASE = 'https://www.safaribooksonline.com/api/v1/book'
    _API_FORMAT = 'json'

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        course_path = mobj.group('course_path')
        course_id = mobj.group('id')

        webpage = self._download_webpage(
            '%s/%s/?override_format=%s' % (self._API_BASE, course_id, self._API_FORMAT),
            course_path, 'Downloading course JSON')

        course_json = json.loads(webpage)

        if 'chapters' not in course_json:
            raise ExtractorError('No chapters found for course %s' % course_id, expected=True)

        num_parts = len(course_json['chapters'])
        parts = ['%02d' % part for part in range(num_parts)]

        entries = [
            self.url_result(
                'https://www.safaribooksonline.com/library/view/%s/%s/part%s.html' % (course_path,
                                                                                      course_id,
                                                                                      part_id),
                'Safari')
            for part_id in parts]

        course_title = course_json['title']

        return self.playlist_result(entries, course_id, course_title)
