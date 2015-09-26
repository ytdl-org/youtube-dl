from __future__ import unicode_literals

import re
import json

from .common import InfoExtractor
from ..compat import (
    compat_str,
    compat_urllib_parse,
    compat_urllib_request,
)
from ..utils import (
    ExtractorError,
    clean_html,
    int_or_none,
)


class LyndaBaseIE(InfoExtractor):
    _LOGIN_URL = 'https://www.lynda.com/login/login.aspx'
    _ACCOUNT_CREDENTIALS_HINT = 'Use --username and --password options to provide lynda.com account credentials.'
    _NETRC_MACHINE = 'lynda'

    def _real_initialize(self):
        self._login()

    def _login(self):
        (username, password) = self._get_login_info()
        if username is None:
            return

        login_form = {
            'username': username.encode('utf-8'),
            'password': password.encode('utf-8'),
            'remember': 'false',
            'stayPut': 'false'
        }
        request = compat_urllib_request.Request(
            self._LOGIN_URL, compat_urllib_parse.urlencode(login_form).encode('utf-8'))
        login_page = self._download_webpage(
            request, None, 'Logging in as %s' % username)

        # Not (yet) logged in
        m = re.search(r'loginResultJson\s*=\s*\'(?P<json>[^\']+)\';', login_page)
        if m is not None:
            response = m.group('json')
            response_json = json.loads(response)
            state = response_json['state']

            if state == 'notlogged':
                raise ExtractorError(
                    'Unable to login, incorrect username and/or password',
                    expected=True)

            # This is when we get popup:
            # > You're already logged in to lynda.com on two devices.
            # > If you log in here, we'll log you out of another device.
            # So, we need to confirm this.
            if state == 'conflicted':
                confirm_form = {
                    'username': '',
                    'password': '',
                    'resolve': 'true',
                    'remember': 'false',
                    'stayPut': 'false',
                }
                request = compat_urllib_request.Request(
                    self._LOGIN_URL, compat_urllib_parse.urlencode(confirm_form).encode('utf-8'))
                login_page = self._download_webpage(
                    request, None,
                    'Confirming log in and log out from another device')

        if all(not re.search(p, login_page) for p in ('isLoggedIn\s*:\s*true', r'logout\.aspx', r'>Log out<')):
            if 'login error' in login_page:
                mobj = re.search(
                    r'(?s)<h1[^>]+class="topmost">(?P<title>[^<]+)</h1>\s*<div>(?P<description>.+?)</div>',
                    login_page)
                if mobj:
                    raise ExtractorError(
                        'lynda returned error: %s - %s'
                        % (mobj.group('title'), clean_html(mobj.group('description'))),
                        expected=True)
            raise ExtractorError('Unable to log in')


class LyndaIE(LyndaBaseIE):
    IE_NAME = 'lynda'
    IE_DESC = 'lynda.com videos'
    _VALID_URL = r'https?://www\.lynda\.com/(?:[^/]+/[^/]+/\d+|player/embed)/(?P<id>\d+)'
    _NETRC_MACHINE = 'lynda'

    _TIMECODE_REGEX = r'\[(?P<timecode>\d+:\d+:\d+[\.,]\d+)\]'

    _TESTS = [{
        'url': 'http://www.lynda.com/Bootstrap-tutorials/Using-exercise-files/110885/114408-4.html',
        'md5': 'ecfc6862da89489161fb9cd5f5a6fac1',
        'info_dict': {
            'id': '114408',
            'ext': 'mp4',
            'title': 'Using the exercise files',
            'duration': 68
        }
    }, {
        'url': 'https://www.lynda.com/player/embed/133770?tr=foo=1;bar=g;fizz=rt&fs=0',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)

        page = self._download_webpage(
            'http://www.lynda.com/ajax/player?videoId=%s&type=video' % video_id,
            video_id, 'Downloading video JSON')
        video_json = json.loads(page)

        if 'Status' in video_json:
            raise ExtractorError(
                'lynda returned error: %s' % video_json['Message'], expected=True)

        if video_json['HasAccess'] is False:
            self.raise_login_required('Video %s is only available for members' % video_id)

        video_id = compat_str(video_json['ID'])
        duration = video_json['DurationInSeconds']
        title = video_json['Title']

        formats = []

        fmts = video_json.get('Formats')
        if fmts:
            formats.extend([
                {
                    'url': fmt['Url'],
                    'ext': fmt['Extension'],
                    'width': fmt['Width'],
                    'height': fmt['Height'],
                    'filesize': fmt['FileSize'],
                    'format_id': str(fmt['Resolution'])
                } for fmt in fmts])

        prioritized_streams = video_json.get('PrioritizedStreams')
        if prioritized_streams:
            formats.extend([
                {
                    'url': video_url,
                    'width': int_or_none(format_id),
                    'format_id': format_id,
                } for format_id, video_url in prioritized_streams['0'].items()
            ])

        self._check_formats(formats, video_id)
        self._sort_formats(formats)

        subtitles = self.extract_subtitles(video_id, page)

        return {
            'id': video_id,
            'title': title,
            'duration': duration,
            'subtitles': subtitles,
            'formats': formats
        }

    def _fix_subtitles(self, subs):
        srt = ''
        seq_counter = 0
        for pos in range(0, len(subs) - 1):
            seq_current = subs[pos]
            m_current = re.match(self._TIMECODE_REGEX, seq_current['Timecode'])
            if m_current is None:
                continue
            seq_next = subs[pos + 1]
            m_next = re.match(self._TIMECODE_REGEX, seq_next['Timecode'])
            if m_next is None:
                continue
            appear_time = m_current.group('timecode')
            disappear_time = m_next.group('timecode')
            text = seq_current['Caption'].strip()
            if text:
                seq_counter += 1
                srt += '%s\r\n%s --> %s\r\n%s\r\n\r\n' % (seq_counter, appear_time, disappear_time, text)
        if srt:
            return srt

    def _get_subtitles(self, video_id, webpage):
        url = 'http://www.lynda.com/ajax/player?videoId=%s&type=transcript' % video_id
        subs = self._download_json(url, None, False)
        if subs:
            return {'en': [{'ext': 'srt', 'data': self._fix_subtitles(subs)}]}
        else:
            return {}


class LyndaCourseIE(LyndaBaseIE):
    IE_NAME = 'lynda:course'
    IE_DESC = 'lynda.com online courses'

    # Course link equals to welcome/introduction video link of same course
    # We will recognize it as course link
    _VALID_URL = r'https?://(?:www|m)\.lynda\.com/(?P<coursepath>[^/]+/[^/]+/(?P<courseid>\d+))-\d\.html'

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        course_path = mobj.group('coursepath')
        course_id = mobj.group('courseid')

        page = self._download_webpage(
            'http://www.lynda.com/ajax/player?courseId=%s&type=course' % course_id,
            course_id, 'Downloading course JSON')
        course_json = json.loads(page)

        if 'Status' in course_json and course_json['Status'] == 'NotFound':
            raise ExtractorError(
                'Course %s does not exist' % course_id, expected=True)

        unaccessible_videos = 0
        videos = []

        # Might want to extract videos right here from video['Formats'] as it seems 'Formats' is not provided
        # by single video API anymore

        for chapter in course_json['Chapters']:
            for video in chapter['Videos']:
                if video['HasAccess'] is False:
                    unaccessible_videos += 1
                    continue
                videos.append(video['ID'])

        if unaccessible_videos > 0:
            self._downloader.report_warning(
                '%s videos are only available for members (or paid members) and will not be downloaded. '
                % unaccessible_videos + self._ACCOUNT_CREDENTIALS_HINT)

        entries = [
            self.url_result(
                'http://www.lynda.com/%s/%s-4.html' % (course_path, video_id),
                'Lynda')
            for video_id in videos]

        course_title = course_json['Title']

        return self.playlist_result(entries, course_id, course_title)
