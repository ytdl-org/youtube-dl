from __future__ import unicode_literals

import re

from .common import InfoExtractor
from .wistia import WistiaIE
from ..compat import compat_str
from ..utils import (
    clean_html,
    ExtractorError,
    get_element_by_class,
    urlencode_postdata,
    urljoin,
)


class UpskillBaseIE(InfoExtractor):
    _LOGIN_URL = 'http://upskillcourses.com/sign_in'
    _NETRC_MACHINE = 'upskill'

    def _real_initialize(self):
        self._login()

    def _login(self):
        username, password = self._get_login_info()
        if username is None:
            return

        login_page, urlh = self._download_webpage_handle(
            self._LOGIN_URL, None, 'Downloading login page')

        login_url = compat_str(urlh.geturl())

        login_form = self._hidden_inputs(login_page)

        login_form.update({
            'user[email]': username,
            'user[password]': password,
        })

        post_url = self._search_regex(
            r'<form[^>]+action=(["\'])(?P<url>(?:(?!\1).)+)\1', login_page,
            'post url', default=login_url, group='url')

        if not post_url.startswith('http'):
            post_url = urljoin(login_url, post_url)

        response = self._download_webpage(
            post_url, None, 'Logging in',
            data=urlencode_postdata(login_form),
            headers={
                'Content-Type': 'application/x-www-form-urlencoded',
                'Referer': login_url,
            })

        # Successful login
        if any(re.search(p, response) for p in (
                r'class=["\']user-signout',
                r'<a[^>]+\bhref=["\']/sign_out',
                r'>\s*Log out\s*<')):
            return

        message = get_element_by_class('alert', response)
        if message is not None:
            raise ExtractorError(
                'Unable to login: %s' % clean_html(message), expected=True)

        raise ExtractorError('Unable to log in')


class UpskillIE(UpskillBaseIE):
    _VALID_URL = r'https?://(?:www\.)?upskillcourses\.com/courses/[^/]+/lectures/(?P<id>\d+)'

    _TESTS = [{
        'url': 'http://upskillcourses.com/courses/essential-web-developer-course/lectures/1747100',
        'info_dict': {
            'id': 'uzw6zw58or',
            'ext': 'mp4',
            'title': 'Welcome to the Course!',
            'description': 'md5:8d66c13403783370af62ca97a7357bdd',
            'duration': 138.763,
            'timestamp': 1479846621,
            'upload_date': '20161122',
        },
        'params': {
            'skip_download': True,
        },
    }, {
        'url': 'http://upskillcourses.com/courses/119763/lectures/1747100',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)

        webpage = self._download_webpage(url, video_id)

        wistia_url = WistiaIE._extract_url(webpage)
        if not wistia_url:
            if any(re.search(p, webpage) for p in (
                    r'class=["\']lecture-contents-locked',
                    r'>\s*Lecture contents locked',
                    r'id=["\']lecture-locked')):
                self.raise_login_required('Lecture contents locked')

        title = self._og_search_title(webpage, default=None)

        return {
            '_type': 'url_transparent',
            'url': wistia_url,
            'ie_key': WistiaIE.ie_key(),
            'title': title,
        }


class UpskillCourseIE(UpskillBaseIE):
    _VALID_URL = r'https?://(?:www\.)?upskillcourses\.com/courses/(?:enrolled/)?(?P<id>[^/?#&]+)'
    _TESTS = [{
        'url': 'http://upskillcourses.com/courses/essential-web-developer-course/',
        'info_dict': {
            'id': '119763',
            'title': 'The Essential Web Developer Course (Free)',
        },
        'playlist_count': 192,
    }, {
        'url': 'http://upskillcourses.com/courses/119763/',
        'only_matching': True,
    }, {
        'url': 'http://upskillcourses.com/courses/enrolled/119763',
        'only_matching': True,
    }]

    @classmethod
    def suitable(cls, url):
        return False if UpskillIE.suitable(url) else super(
            UpskillCourseIE, cls).suitable(url)

    def _real_extract(self, url):
        course_id = self._match_id(url)

        webpage = self._download_webpage(url, course_id)

        course_id = self._search_regex(
            r'data-course-id=["\'](\d+)', webpage, 'course id',
            default=course_id)

        entries = []

        for mobj in re.finditer(
                r'(?s)(?P<li><li[^>]+class=(["\'])(?:(?!\2).)*?section-item[^>]+>.+?</li>)',
                webpage):
            li = mobj.group('li')
            if 'fa-youtube-play' not in li:
                continue
            lecture_url = self._search_regex(
                r'<a[^>]+href=(["\'])(?P<url>(?:(?!\1).)+)\1', li,
                'lecture url', default=None, group='url')
            if not lecture_url:
                continue
            lecture_id = self._search_regex(
                r'/lectures/(\d+)', lecture_url, 'lecture id', default=None)
            title = self._html_search_regex(
                r'<span[^>]+class=["\']lecture-name[^>]+>([^<]+)', li,
                'title', default=None)
            entries.append(
                self.url_result(
                    urljoin('http://upskillcourses.com/', lecture_url),
                    ie=UpskillIE.ie_key(), video_id=lecture_id,
                    video_title=clean_html(title)))

        course_title = self._html_search_regex(
            (r'(?s)<img[^>]+class=["\']course-image[^>]+>\s*<h\d>(.+?)</h',
             r'(?s)<h\d[^>]+class=["\']course-title[^>]+>(.+?)</h'),
            webpage, 'course title', fatal=False)

        return self.playlist_result(entries, course_id, course_title)
