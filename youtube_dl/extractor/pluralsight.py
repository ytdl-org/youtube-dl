from __future__ import unicode_literals

import collections
import json
import os
import random
import re

from .common import InfoExtractor
from ..compat import (
    compat_str,
    compat_urlparse,
)
from ..utils import (
    ExtractorError,
    float_or_none,
    int_or_none,
    parse_duration,
    qualities,
    srt_subtitles_timecode,
    urlencode_postdata,
)


class PluralsightBaseIE(InfoExtractor):
    _API_BASE = 'http://app.pluralsight.com'


class PluralsightIE(PluralsightBaseIE):
    IE_NAME = 'pluralsight'
    _VALID_URL = r'https?://(?:(?:www|app)\.)?pluralsight\.com/training/player\?'
    _LOGIN_URL = 'https://app.pluralsight.com/id/'

    _NETRC_MACHINE = 'pluralsight'

    _TESTS = [{
        'url': 'http://www.pluralsight.com/training/player?author=mike-mckeown&name=hosting-sql-server-windows-azure-iaas-m7-mgmt&mode=live&clip=3&course=hosting-sql-server-windows-azure-iaas',
        'md5': '4d458cf5cf4c593788672419a8dd4cf8',
        'info_dict': {
            'id': 'hosting-sql-server-windows-azure-iaas-m7-mgmt-04',
            'ext': 'mp4',
            'title': 'Management of SQL Server - Demo Monitoring',
            'duration': 338,
        },
        'skip': 'Requires pluralsight account credentials',
    }, {
        'url': 'https://app.pluralsight.com/training/player?course=angularjs-get-started&author=scott-allen&name=angularjs-get-started-m1-introduction&clip=0&mode=live',
        'only_matching': True,
    }, {
        # available without pluralsight account
        'url': 'http://app.pluralsight.com/training/player?author=scott-allen&name=angularjs-get-started-m1-introduction&mode=live&clip=0&course=angularjs-get-started',
        'only_matching': True,
    }]

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
            'Username': username,
            'Password': password,
        })

        post_url = self._search_regex(
            r'<form[^>]+action=(["\'])(?P<url>.+?)\1', login_page,
            'post url', default=self._LOGIN_URL, group='url')

        if not post_url.startswith('http'):
            post_url = compat_urlparse.urljoin(self._LOGIN_URL, post_url)

        response = self._download_webpage(
            post_url, None, 'Logging in as %s' % username,
            data=urlencode_postdata(login_form),
            headers={'Content-Type': 'application/x-www-form-urlencoded'})

        error = self._search_regex(
            r'<span[^>]+class="field-validation-error"[^>]*>([^<]+)</span>',
            response, 'error message', default=None)
        if error:
            raise ExtractorError('Unable to login: %s' % error, expected=True)

        if all(p not in response for p in ('__INITIAL_STATE__', '"currentUser"')):
            raise ExtractorError('Unable to log in')

    def _get_subtitles(self, author, clip_id, lang, name, duration, video_id):
        captions_post = {
            'a': author,
            'cn': clip_id,
            'lc': lang,
            'm': name,
        }
        captions = self._download_json(
            '%s/training/Player/Captions' % self._API_BASE, video_id,
            'Downloading captions JSON', 'Unable to download captions JSON',
            fatal=False, data=json.dumps(captions_post).encode('utf-8'),
            headers={'Content-Type': 'application/json;charset=utf-8'})
        if captions:
            return {
                lang: [{
                    'ext': 'json',
                    'data': json.dumps(captions),
                }, {
                    'ext': 'srt',
                    'data': self._convert_subtitles(duration, captions),
                }]
            }

    @staticmethod
    def _convert_subtitles(duration, subs):
        srt = ''
        for num, current in enumerate(subs):
            current = subs[num]
            start, text = float_or_none(
                current.get('DisplayTimeOffset')), current.get('Text')
            if start is None or text is None:
                continue
            end = duration if num == len(subs) - 1 else float_or_none(
                subs[num + 1].get('DisplayTimeOffset'))
            if end is None:
                continue
            srt += os.linesep.join(
                (
                    '%d' % num,
                    '%s --> %s' % (
                        srt_subtitles_timecode(start),
                        srt_subtitles_timecode(end)),
                    text,
                    os.linesep,
                ))
        return srt

    def _real_extract(self, url):
        qs = compat_urlparse.parse_qs(compat_urlparse.urlparse(url).query)

        author = qs.get('author', [None])[0]
        name = qs.get('name', [None])[0]
        clip_id = qs.get('clip', [None])[0]
        course = qs.get('course', [None])[0]

        if any(not f for f in (author, name, clip_id, course,)):
            raise ExtractorError('Invalid URL', expected=True)

        display_id = '%s-%s' % (name, clip_id)

        webpage = self._download_webpage(url, display_id)

        modules = self._search_regex(
            r'moduleCollection\s*:\s*new\s+ModuleCollection\((\[.+?\])\s*,\s*\$rootScope\)',
            webpage, 'modules', default=None)

        if modules:
            collection = self._parse_json(modules, display_id)
        else:
            # Webpage may be served in different layout (see
            # https://github.com/rg3/youtube-dl/issues/7607)
            collection = self._parse_json(
                self._search_regex(
                    r'var\s+initialState\s*=\s*({.+?});\n', webpage, 'initial state'),
                display_id)['course']['modules']

        module, clip = None, None

        for module_ in collection:
            if name in (module_.get('moduleName'), module_.get('name')):
                module = module_
                for clip_ in module_.get('clips', []):
                    clip_index = clip_.get('clipIndex')
                    if clip_index is None:
                        clip_index = clip_.get('index')
                    if clip_index is None:
                        continue
                    if compat_str(clip_index) == clip_id:
                        clip = clip_
                        break

        if not clip:
            raise ExtractorError('Unable to resolve clip')

        title = '%s - %s' % (module['title'], clip['title'])

        QUALITIES = {
            'low': {'width': 640, 'height': 480},
            'medium': {'width': 848, 'height': 640},
            'high': {'width': 1024, 'height': 768},
            'high-widescreen': {'width': 1280, 'height': 720},
        }

        QUALITIES_PREFERENCE = ('low', 'medium', 'high', 'high-widescreen',)
        quality_key = qualities(QUALITIES_PREFERENCE)

        AllowedQuality = collections.namedtuple('AllowedQuality', ['ext', 'qualities'])

        ALLOWED_QUALITIES = (
            AllowedQuality('webm', ['high', ]),
            AllowedQuality('mp4', ['low', 'medium', 'high', ]),
        )

        # Some courses also offer widescreen resolution for high quality (see
        # https://github.com/rg3/youtube-dl/issues/7766)
        widescreen = True if re.search(
            r'courseSupportsWidescreenVideoFormats\s*:\s*true', webpage) else False
        best_quality = 'high-widescreen' if widescreen else 'high'
        if widescreen:
            for allowed_quality in ALLOWED_QUALITIES:
                allowed_quality.qualities.append(best_quality)

        # In order to minimize the number of calls to ViewClip API and reduce
        # the probability of being throttled or banned by Pluralsight we will request
        # only single format until formats listing was explicitly requested.
        if self._downloader.params.get('listformats', False):
            allowed_qualities = ALLOWED_QUALITIES
        else:
            def guess_allowed_qualities():
                req_format = self._downloader.params.get('format') or 'best'
                req_format_split = req_format.split('-', 1)
                if len(req_format_split) > 1:
                    req_ext, req_quality = req_format_split
                    for allowed_quality in ALLOWED_QUALITIES:
                        if req_ext == allowed_quality.ext and req_quality in allowed_quality.qualities:
                            return (AllowedQuality(req_ext, (req_quality, )), )
                req_ext = 'webm' if self._downloader.params.get('prefer_free_formats') else 'mp4'
                return (AllowedQuality(req_ext, (best_quality, )), )
            allowed_qualities = guess_allowed_qualities()

        formats = []
        for ext, qualities_ in allowed_qualities:
            for quality in qualities_:
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
                format_id = '%s-%s' % (ext, quality)
                clip_url = self._download_webpage(
                    '%s/training/Player/ViewClip' % self._API_BASE, display_id,
                    'Downloading %s URL' % format_id, fatal=False,
                    data=json.dumps(clip_post).encode('utf-8'),
                    headers={'Content-Type': 'application/json;charset=utf-8'})

                # Pluralsight tracks multiple sequential calls to ViewClip API and start
                # to return 429 HTTP errors after some time (see
                # https://github.com/rg3/youtube-dl/pull/6989). Moreover it may even lead
                # to account ban (see https://github.com/rg3/youtube-dl/issues/6842).
                # To somewhat reduce the probability of these consequences
                # we will sleep random amount of time before each call to ViewClip.
                self._sleep(
                    random.randint(2, 5), display_id,
                    '%(video_id)s: Waiting for %(timeout)s seconds to avoid throttling')

                if not clip_url:
                    continue
                f.update({
                    'url': clip_url,
                    'ext': ext,
                    'format_id': format_id,
                    'quality': quality_key(quality),
                })
                formats.append(f)
        self._sort_formats(formats)

        duration = int_or_none(
            clip.get('duration')) or parse_duration(clip.get('formattedDuration'))

        # TODO: other languages?
        subtitles = self.extract_subtitles(
            author, clip_id, 'en', name, duration, display_id)

        return {
            'id': clip.get('clipName') or clip['name'],
            'title': title,
            'duration': duration,
            'creator': author,
            'formats': formats,
            'subtitles': subtitles,
        }


class PluralsightCourseIE(PluralsightBaseIE):
    IE_NAME = 'pluralsight:course'
    _VALID_URL = r'https?://(?:(?:www|app)\.)?pluralsight\.com/(?:library/)?courses/(?P<id>[^/]+)'
    _TESTS = [{
        # Free course from Pluralsight Starter Subscription for Microsoft TechNet
        # https://offers.pluralsight.com/technet?loc=zTS3z&prod=zOTprodz&tech=zOttechz&prog=zOTprogz&type=zSOz&media=zOTmediaz&country=zUSz
        'url': 'http://www.pluralsight.com/courses/hosting-sql-server-windows-azure-iaas',
        'info_dict': {
            'id': 'hosting-sql-server-windows-azure-iaas',
            'title': 'Hosting SQL Server in Microsoft Azure IaaS Fundamentals',
            'description': 'md5:61b37e60f21c4b2f91dc621a977d0986',
        },
        'playlist_count': 31,
    }, {
        # available without pluralsight account
        'url': 'https://www.pluralsight.com/courses/angularjs-get-started',
        'only_matching': True,
    }, {
        'url': 'https://app.pluralsight.com/library/courses/understanding-microsoft-azure-amazon-aws/table-of-contents',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        course_id = self._match_id(url)

        # TODO: PSM cookie

        course = self._download_json(
            '%s/data/course/%s' % (self._API_BASE, course_id),
            course_id, 'Downloading course JSON')

        title = course['title']
        description = course.get('description') or course.get('shortDescription')

        course_data = self._download_json(
            '%s/data/course/content/%s' % (self._API_BASE, course_id),
            course_id, 'Downloading course data JSON')

        entries = []
        for num, module in enumerate(course_data, 1):
            for clip in module.get('clips', []):
                player_parameters = clip.get('playerParameters')
                if not player_parameters:
                    continue
                entries.append({
                    '_type': 'url_transparent',
                    'url': '%s/training/player?%s' % (self._API_BASE, player_parameters),
                    'ie_key': PluralsightIE.ie_key(),
                    'chapter': module.get('title'),
                    'chapter_number': num,
                    'chapter_id': module.get('moduleRef'),
                })

        return self.playlist_result(entries, course_id, title, description)
