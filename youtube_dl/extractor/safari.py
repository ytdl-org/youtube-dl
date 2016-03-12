# encoding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from .brightcove import BrightcoveLegacyIE

from ..utils import (
    ExtractorError,
    sanitized_Request,
    smuggle_url,
    std_headers,
    urlencode_postdata,
    update_url_query,
)


class SafariBaseIE(InfoExtractor):
    _LOGIN_URL = 'https://www.safaribooksonline.com/accounts/login/'
    _SUCCESSFUL_LOGIN_REGEX = r'<a href="/accounts/logout/"[^>]*>Sign Out</a>'
    _NETRC_MACHINE = 'safari'

    _API_BASE = 'https://www.safaribooksonline.com/api/v1'
    _API_FORMAT = 'json'

    LOGGED_IN = False

    def _real_initialize(self):
        self._login()

    def _login(self):
        # We only need to log in once for courses or individual videos
        if self.LOGGED_IN:
            return

        (username, password) = self._get_login_info()
        if username is None:
            return

        headers = std_headers.copy()
        if 'Referer' not in headers:
            headers['Referer'] = self._LOGIN_URL
        login_page_request = sanitized_Request(self._LOGIN_URL, headers=headers)

        login_page = self._download_webpage(
            login_page_request, None,
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

        request = sanitized_Request(
            self._LOGIN_URL, urlencode_postdata(login_form), headers=headers)
        login_page = self._download_webpage(
            request, None, 'Logging in as %s' % username)

        if re.search(self._SUCCESSFUL_LOGIN_REGEX, login_page) is None:
            raise ExtractorError(
                'Login failed; make sure your credentials are correct and try again.',
                expected=True)

        SafariBaseIE.LOGGED_IN = True

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
        'md5': 'dcc5a425e79f2564148652616af1f2a3',
        'info_dict': {
            'id': '0_qbqx90ic',
            'ext': 'mp4',
            'title': 'Introduction to Hadoop Fundamentals LiveLessons',
            'timestamp': 1437758058,
            'upload_date': '20150724',
            'uploader_id': 'stork',
        },
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

        webpage = self._download_webpage(url, '%s/%s' % (course_id, part))
        reference_id = self._search_regex(r'data-reference-id="([^"]+)"', webpage, 'kaltura reference id')
        partner_id = self._search_regex(r'data-partner-id="([^"]+)"', webpage, 'kaltura widget id')
        ui_id = self._search_regex(r'data-ui-id="([^"]+)"', webpage, 'kaltura uiconf id')

        query = {
            'wid': '_%s' % partner_id,
            'uiconf_id': ui_id,
            'flashvars[referenceId]': reference_id,
        }

        if self.LOGGED_IN:
            kaltura_session = self._download_json(
                '%s/player/kaltura_session/?reference_id=%s' % (self._API_BASE, reference_id),
                course_id, 'Downloading kaltura session JSON',
                'Unable to download kaltura session JSON', fatal=False)
            if kaltura_session:
                session = kaltura_session.get('session')
                if session:
                    query['flashvars[ks]'] = session

        return self.url_result(update_url_query(
            'https://cdnapisec.kaltura.com/html5/html5lib/v2.37.1/mwEmbedFrame.php', query),
            'Kaltura')


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
            '%s/book/%s/?override_format=%s' % (self._API_BASE, course_id, self._API_FORMAT),
            course_id, 'Downloading course JSON')

        if 'chapters' not in course_json:
            raise ExtractorError(
                'No chapters found for course %s' % course_id, expected=True)

        entries = [
            self.url_result(chapter, 'Safari')
            for chapter in course_json['chapters']]

        course_title = course_json['title']

        return self.playlist_result(entries, course_id, course_title)
