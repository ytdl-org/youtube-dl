from __future__ import unicode_literals

import re
import json

from .common import InfoExtractor
from ..compat import (
    compat_str,
    compat_urllib_parse,
    compat_urllib_request,
    compat_urlparse,
)
from ..utils import (
    ExtractorError,
    int_or_none,
    parse_duration,
)


class PluralsightIE(InfoExtractor):
    IE_NAME = 'pluralsight'
    _VALID_URL = r'https?://(?:www\.)?pluralsight\.com/training/player\?author=(?P<author>[^&]+)&name=(?P<name>[^&]+)(?:&mode=live)?&clip=(?P<clip>\d+)&course=(?P<course>[^&]+)'
    _LOGIN_URL = 'https://www.pluralsight.com/id/'
    _NETRC_MACHINE = 'pluralsight'

    _TEST = {
        'url': 'http://www.pluralsight.com/training/player?author=mike-mckeown&name=hosting-sql-server-windows-azure-iaas-m7-mgmt&mode=live&clip=3&course=hosting-sql-server-windows-azure-iaas',
        'md5': '4d458cf5cf4c593788672419a8dd4cf8',
        'info_dict': {
            'id': 'hosting-sql-server-windows-azure-iaas-m7-mgmt-04',
            'ext': 'mp4',
            'title': 'Management of SQL Server - Demo Monitoring',
            'duration': 338,
        },
        'skip': 'Requires pluralsight account credentials',
    }

    def _real_initialize(self):
        self._login()

    def _login(self):
        (username, password) = self._get_login_info()
        if username is None:
            self.raise_login_required('Pluralsight account is required')

        login_page = self._download_webpage(
            self._LOGIN_URL, None, 'Downloading login page')

        login_form = self._hidden_inputs(login_page)

        login_form.update({
            'Username': username.encode('utf-8'),
            'Password': password.encode('utf-8'),
        })

        post_url = self._search_regex(
            r'<form[^>]+action=(["\'])(?P<url>.+?)\1', login_page,
            'post url', default=self._LOGIN_URL, group='url')

        if not post_url.startswith('http'):
            post_url = compat_urlparse.urljoin(self._LOGIN_URL, post_url)

        request = compat_urllib_request.Request(
            post_url, compat_urllib_parse.urlencode(login_form).encode('utf-8'))
        request.add_header('Content-Type', 'application/x-www-form-urlencoded')

        response = self._download_webpage(
            request, None, 'Logging in as %s' % username)

        error = self._search_regex(
            r'<span[^>]+class="field-validation-error"[^>]*>([^<]+)</span>',
            response, 'error message', default=None)
        if error:
            raise ExtractorError('Unable to login: %s' % error, expected=True)

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        author = mobj.group('author')
        name = mobj.group('name')
        clip_id = mobj.group('clip')
        course = mobj.group('course')

        display_id = '%s-%s' % (name, clip_id)

        webpage = self._download_webpage(url, display_id)

        collection = self._parse_json(
            self._search_regex(
                r'moduleCollection\s*:\s*new\s+ModuleCollection\((\[.+?\])\s*,\s*\$rootScope\)',
                webpage, 'modules'),
            display_id)

        module, clip = None, None

        for module_ in collection:
            if module_.get('moduleName') == name:
                module = module_
                for clip_ in module_.get('clips', []):
                    clip_index = clip_.get('clipIndex')
                    if clip_index is None:
                        continue
                    if compat_str(clip_index) == clip_id:
                        clip = clip_
                        break

        if not clip:
            raise ExtractorError('Unable to resolve clip')

        QUALITIES = {
            'low': {'width': 640, 'height': 480},
            'medium': {'width': 848, 'height': 640},
            'high': {'width': 1024, 'height': 768},
        }

        ALLOWED_QUALITIES = (
            ('webm', ('high',)),
            ('mp4', ('low', 'medium', 'high',)),
        )

        formats = []
        for ext, qualities in ALLOWED_QUALITIES:
            for quality in qualities:
                f = QUALITIES[quality].copy()
                clip_post = {
                    'a': author,
                    'cap': 'false',
                    'cn': clip_id,
                    'course': course,
                    'lc': 'en',
                    'm': name,
                    'mt': ext,
                    'q': '%dx%d' % (f['width'], f['height']),
                }
                request = compat_urllib_request.Request(
                    'http://www.pluralsight.com/training/Player/ViewClip',
                    json.dumps(clip_post).encode('utf-8'))
                request.add_header('Content-Type', 'application/json;charset=utf-8')
                format_id = '%s-%s' % (ext, quality)
                clip_url = self._download_webpage(
                    request, display_id, 'Downloading %s URL' % format_id, fatal=False)
                if not clip_url:
                    continue
                f.update({
                    'url': clip_url,
                    'ext': ext,
                    'format_id': format_id,
                })
                formats.append(f)
        self._sort_formats(formats)

        # TODO: captions
        # http://www.pluralsight.com/training/Player/ViewClip + cap = true
        # or
        # http://www.pluralsight.com/training/Player/Captions
        # { a = author, cn = clip_id, lc = end, m = name }

        return {
            'id': clip['clipName'],
            'title': '%s - %s' % (module['title'], clip['title']),
            'duration': int_or_none(clip.get('duration')) or parse_duration(clip.get('formattedDuration')),
            'creator': author,
            'formats': formats
        }


class PluralsightCourseIE(InfoExtractor):
    IE_NAME = 'pluralsight:course'
    _VALID_URL = r'https?://(?:www\.)?pluralsight\.com/courses/(?P<id>[^/]+)'
    _TEST = {
        # Free course from Pluralsight Starter Subscription for Microsoft TechNet
        # https://offers.pluralsight.com/technet?loc=zTS3z&prod=zOTprodz&tech=zOttechz&prog=zOTprogz&type=zSOz&media=zOTmediaz&country=zUSz
        'url': 'http://www.pluralsight.com/courses/hosting-sql-server-windows-azure-iaas',
        'info_dict': {
            'id': 'hosting-sql-server-windows-azure-iaas',
            'title': 'Hosting SQL Server in Microsoft Azure IaaS Fundamentals',
            'description': 'md5:61b37e60f21c4b2f91dc621a977d0986',
        },
        'playlist_count': 31,
    }

    def _real_extract(self, url):
        course_id = self._match_id(url)

        # TODO: PSM cookie

        course = self._download_json(
            'http://www.pluralsight.com/data/course/%s' % course_id,
            course_id, 'Downloading course JSON')

        title = course['title']
        description = course.get('description') or course.get('shortDescription')

        course_data = self._download_json(
            'http://www.pluralsight.com/data/course/content/%s' % course_id,
            course_id, 'Downloading course data JSON')

        entries = []
        for module in course_data:
            for clip in module.get('clips', []):
                player_parameters = clip.get('playerParameters')
                if not player_parameters:
                    continue
                entries.append(self.url_result(
                    'http://www.pluralsight.com/training/player?%s' % player_parameters,
                    'Pluralsight'))

        return self.playlist_result(entries, course_id, title, description)
