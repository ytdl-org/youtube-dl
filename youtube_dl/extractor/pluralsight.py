from __future__ import unicode_literals

import collections
import json
import os
import random

from .common import InfoExtractor
from ..compat import (
    compat_str,
    compat_urlparse,
)
from ..utils import (
    dict_get,
    ExtractorError,
    float_or_none,
    int_or_none,
    parse_duration,
    qualities,
    srt_subtitles_timecode,
    update_url_query,
    urlencode_postdata,
)


class PluralsightBaseIE(InfoExtractor):
    _API_BASE = 'https://app.pluralsight.com'


class PluralsightIE(PluralsightBaseIE):
    IE_NAME = 'pluralsight'
    _VALID_URL = r'https?://(?:(?:www|app)\.)?pluralsight\.com/(?:training/)?player\?'
    _LOGIN_URL = 'https://app.pluralsight.com/id/'

    _NETRC_MACHINE = 'pluralsight'

    _TESTS = [{
        'url': 'http://www.pluralsight.com/training/player?author=mike-mckeown&name=hosting-sql-server-windows-azure-iaas-m7-mgmt&mode=live&clip=3&course=hosting-sql-server-windows-azure-iaas',
        'md5': '4d458cf5cf4c593788672419a8dd4cf8',
        'info_dict': {
            'id': 'hosting-sql-server-windows-azure-iaas-m7-mgmt-04',
            'ext': 'mp4',
            'title': 'Demo Monitoring',
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
    }, {
        'url': 'https://app.pluralsight.com/player?course=ccna-intro-networking&author=ross-bagurdes&name=ccna-intro-networking-m06&clip=0',
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
            BLOCKED = 'Your account has been blocked due to suspicious activity'
            if BLOCKED in response:
                raise ExtractorError(
                    'Unable to login: %s' % BLOCKED, expected=True)
            raise ExtractorError('Unable to log in')

    def _get_subtitles(self, author, clip_id, lang, name, duration, video_id):
        captions_post = {
            'a': author,
            'cn': clip_id,
            'lc': lang,
            'm': name,
        }
        captions = self._download_json(
            '%s/player/retrieve-captions' % self._API_BASE, video_id,
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
        TIME_OFFSET_KEYS = ('displayTimeOffset', 'DisplayTimeOffset')
        TEXT_KEYS = ('text', 'Text')
        for num, current in enumerate(subs):
            current = subs[num]
            start, text = (
                float_or_none(dict_get(current, TIME_OFFSET_KEYS)),
                dict_get(current, TEXT_KEYS))
            if start is None or text is None:
                continue
            end = duration if num == len(subs) - 1 else float_or_none(
                dict_get(subs[num + 1], TIME_OFFSET_KEYS))
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
        course_name = qs.get('course', [None])[0]

        if any(not f for f in (author, name, clip_id, course_name,)):
            raise ExtractorError('Invalid URL', expected=True)

        display_id = '%s-%s' % (name, clip_id)

        course = self._download_json(
            'https://app.pluralsight.com/player/user/api/v1/player/payload',
            display_id, data=urlencode_postdata({'courseId': course_name}),
            headers={'Referer': url})

        collection = course['modules']

        clip = None

        for module_ in collection:
            if name in (module_.get('moduleName'), module_.get('name')):
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

        title = clip['title']

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
        widescreen = course.get('supportsWideScreenVideoFormats') is True
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
                    'author': author,
                    'includeCaptions': False,
                    'clipIndex': int(clip_id),
                    'courseName': course_name,
                    'locale': 'en',
                    'moduleName': name,
                    'mediaType': ext,
                    'quality': '%dx%d' % (f['width'], f['height']),
                }
                format_id = '%s-%s' % (ext, quality)
                viewclip = self._download_json(
                    '%s/video/clips/viewclip' % self._API_BASE, display_id,
                    'Downloading %s viewclip JSON' % format_id, fatal=False,
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

                if not viewclip:
                    continue

                clip_urls = viewclip.get('urls')
                if not isinstance(clip_urls, list):
                    continue

                for clip_url_data in clip_urls:
                    clip_url = clip_url_data.get('url')
                    if not clip_url:
                        continue
                    cdn = clip_url_data.get('cdn')
                    clip_f = f.copy()
                    clip_f.update({
                        'url': clip_url,
                        'ext': ext,
                        'format_id': '%s-%s' % (format_id, cdn) if cdn else format_id,
                        'quality': quality_key(quality),
                        'source_preference': int_or_none(clip_url_data.get('rank')),
                    })
                    formats.append(clip_f)

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
            '%s/player/functions/rpc' % self._API_BASE, course_id,
            'Downloading course JSON',
            data=json.dumps({
                'fn': 'bootstrapPlayer',
                'payload': {
                    'courseId': course_id,
                }
            }).encode('utf-8'),
            headers={
                'Content-Type': 'application/json;charset=utf-8'
            })['payload']['course']

        title = course['title']
        course_name = course['name']
        course_data = course['modules']
        description = course.get('description') or course.get('shortDescription')

        entries = []
        for num, module in enumerate(course_data, 1):
            author = module.get('author')
            module_name = module.get('name')
            if not author or not module_name:
                continue
            for clip in module.get('clips', []):
                clip_index = int_or_none(clip.get('index'))
                if clip_index is None:
                    continue
                clip_url = update_url_query(
                    '%s/player' % self._API_BASE, query={
                        'mode': 'live',
                        'course': course_name,
                        'author': author,
                        'name': module_name,
                        'clip': clip_index,
                    })
                entries.append({
                    '_type': 'url_transparent',
                    'url': clip_url,
                    'ie_key': PluralsightIE.ie_key(),
                    'chapter': module.get('title'),
                    'chapter_number': num,
                    'chapter_id': module.get('moduleRef'),
                })

        return self.playlist_result(entries, course_id, title, description)
