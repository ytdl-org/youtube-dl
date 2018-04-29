# coding: utf-8
from __future__ import unicode_literals

import collections

import re

from .common import InfoExtractor
from ..compat import (
    compat_urlparse,
    compat_str)

from ..utils import (
    ExtractorError,
    urlencode_postdata,
    qualities
)


class FrontEndMasterBaseIE(InfoExtractor):
    _API_BASE = 'https://api.frontendmasters.com/v1/kabuki/courses'
    _VIDEO_BASE = 'http://www.frontendmasters.com/courses'
    _COOKIES_BASE = 'https://api.frontendmasters.com'
    _LOGIN_URL = 'https://frontendmasters.com/login/'
    _SUPPORTED_MEAN = {
        "resolution": [360, 720, 1080],
        "format": ['webm', 'mp4']
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

        logout_link = self._search_regex('(Logout .*)',
                                         response, 'logout-link')
        if not logout_link:
            raise ExtractorError('Unable to login', expected=True)

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

    def _pair_section_with_video_elemen_index(self, lesson_elements):
        sections = {}
        current_section = None
        current_section_number = 0
        for elem in lesson_elements:
            if isinstance(elem, unicode):
                (current_section, current_section_number) = \
                    (elem.encode('utf-8'), current_section_number + 1)
            else:
                if current_section:
                    sections[elem] = (current_section, current_section_number)

        return sections


class FrontEndMasterIE(FrontEndMasterBaseIE):
    IE_NAME = 'frontend-masters'

    _VALID_URL = r'https?://(?:www\.)?frontendmasters\.com/courses/(?P<courseid>[a-z\-]+)/(?P<id>[a-z\-]+)/?'
    _NETRC_MACHINE = 'frontend-masters'
    _TEST = {
        'url': 'https://frontendmasters.com/courses/content-strategy/introduction/',
        'md5': '5f176d4f170778524f40a06307a929f6',
        'info_dict': {
            'id': 'introduction',
            'title': 'Introduction',
            'display_id': 'content-strategy',
            'ext': 'mp4'
        },
        'skip': 'Requires FrontendMasters account credentials'
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        course_id = self._match_course_id(url)
        course_json_content = self._download_course(course_id=course_id,
                                                    url=url,
                                                    display_id=course_id)

        lesson_index = course_json_content.get('lessonSlugs').index(video_id)
        lesson_hash = course_json_content.get('lessonHashes')[lesson_index]
        lesson_section_elements = course_json_content.get('lessonElements')
        lesson_data = course_json_content.get('lessonData')[lesson_hash]
        lesson_source_base = lesson_data.get('sourceBase')
        course_sections_pairing = self._pair_section_with_video_elemen_index(lesson_section_elements)

        lesson_title = lesson_data.get('title')
        lesson_description = lesson_data.get('description')
        lesson_index = lesson_data.get('index')
        lesson_slug = lesson_data.get('slug')
        lesson_thumbnail_url = lesson_data.get('thumbnail')
        lesson_section = course_sections_pairing.get(lesson_index)[0]
        lesson_section_number = course_sections_pairing.get(lesson_index)[1]


        QUALITIES_PREFERENCE = ('low', 'medium', 'high')
        quality_key = qualities(QUALITIES_PREFERENCE)
        QUALITIES = {
            'low': {'width': 480, 'height': 360},
            'medium': {'width': 1280, 'height': 720},
            'high': {'width': 1920, 'height': 1080}
        }

        AllowedQuality = collections.namedtuple('AllowedQuality', ['ext', 'qualities'])
        ALLOWED_QUALITIES = [
            AllowedQuality('webm', ['low', 'medium', 'high']),
            AllowedQuality('mp4', ['low', 'medium', 'high'])
        ]

        cookies = self._get_cookies(self._COOKIES_BASE)
        cookies_str = ";".join(["%s=%s" % (cookie.key, cookie.value)
                                for cookie in cookies.values()])
        video_request_url = "%s/source"
        video_request_headers = {
            "origin": "https://frontendmasters.com",
            "referer": lesson_source_base,
            "cookie": cookies_str,
            'user-agent': "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/66.0.3359.117 Safari/537.36"
        }

        if self._downloader.params.get('listformats', False):
            allowed_qualities = ALLOWED_QUALITIES
        else:
            def guess_allowed_qualities():
                req_format = self._downloader.params.get('format') or 'best'
                req_format_split = req_format.split('-', 1)
                if len(req_format_split) > 1:
                    req_ext, req_quality = req_format_split
                    req_quality = '-'.join(req_quality.split('-')[:2])
                    for allowed_quality in ALLOWED_QUALITIES:
                        if req_ext == allowed_quality.ext and req_quality in allowed_quality.qualities:
                            return (AllowedQuality(req_ext, (req_quality, )), )
                req_ext = 'webm' if self._downloader.params.get('prefer_free_formats') else 'mp4'
                return (AllowedQuality(req_ext, ('high', )), )
            allowed_qualities = guess_allowed_qualities()

        formats = []
        for ext, qualities_ in allowed_qualities:
            for quality in qualities_:
                f = QUALITIES[quality].copy()
                video_request_params = {
                    'r': f['height'],
                    'f': ext
                }
                video_response = self._download_json(video_request_url % lesson_source_base, video_id,
                                                     query=video_request_params, headers=video_request_headers)

                # To avoid the possibility of problems with multiple sequential calls to ViewClip API and start
                # to return 429 HTTP errors after some time (see the problem Pluralsight has on
                # https://github.com/rg3/youtube-dl/pull/6989) and avoid also the risk of
                # account ban (see https://github.com/rg3/youtube-dl/issues/6842),
                # we will sleep random amount of time before each call to ViewClip.

                # self._sleep(
                #     random.randint(2, 5), lesson_slug,
                #     '%(video_id)s: Waiting for %(timeout)s seconds to avoid throttling')
                #
                # if not video_response:
                #     continue

                video_url = video_response.get('url')
                clip_f = f.copy()
                clip_f.update({
                    'url': video_url,
                    'ext': ext,
                    'format_id': '%s-%s' % (ext, quality),
                    'quality': quality_key(quality),
                    'height': f['height']
                })
                formats.append(clip_f)

        self._sort_formats(formats)

        return {
            'id': video_id,
            'display_id': lesson_slug,
            'title': lesson_title,
            'description': lesson_description,
            'chapter': lesson_section,
            'chapter_number': lesson_section_number,
            'thumbnail': lesson_thumbnail_url,
            'formats': formats
        }


class FrontEndMasterCourseIE(FrontEndMasterBaseIE):
    IE_NAME = 'frontend-masters:course'
    IE_DESC = "frontendmasters.com online courses"

    _VALID_URL = r'https?://(?:www\.)?frontendmasters\.com/courses/(?P<id>[a-z\-]+)/?'
    _NETRC_MACHINE = 'frontend-masters'
    _TESTS = [{
        'url': 'https://frontendmasters.com/courses/content-strategy/',
        'info_dict': {
            'id': 'content-strategy',
            'title': 'Content Strategy',
            'description': 'md5:7916149d4539c5d6fa86ff43a5df213b'
        },
        'playlist_count': 31,
    }, {
        'url': 'https://frontendmasters.com/courses/sql-fundamentals/',
        'only_matching': True,
    }, {
        'url': 'https://frontendmasters.com/courses/introduction-to-javascript-jquery/',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        course_id = self._match_id(url)
        course_json_content = self._download_course(course_id=course_id,
                                                    url=url,
                                                    display_id=None)

        title = course_json_content.get('title')
        description = course_json_content.get('description')
        course_display_id = course_json_content.get('slug')

        videos_data = course_json_content.get('lessonData').values()
        videos_data = sorted(videos_data, key=lambda video: video.get('index'))

        entries = []
        for video in videos_data:
            video_slug = video.get('slug')
            clip_url = "%s/%s/%s" % (self._VIDEO_BASE, course_display_id, video_slug)
            entries.append({
                '_type': 'url_transparent',
                'url': clip_url,
                'ie_key': FrontEndMasterIE.ie_key()
            })

        return self.playlist_result(entries, course_id, title, description)
