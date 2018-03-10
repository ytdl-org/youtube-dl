from __future__ import unicode_literals

import re

from .common import InfoExtractor
from .vimeo import VimeoIE
from ..utils import (
    extract_attributes,
    ExtractorError,
    smuggle_url,
    unsmuggle_url,
    urljoin,
)


class RayWenderlichIE(InfoExtractor):
    _VALID_URL = r'https?://videos\.raywenderlich\.com/courses/(?P<course_id>[^/]+)/lessons/(?P<id>\d+)'

    _TESTS = [{
        'url': 'https://videos.raywenderlich.com/courses/105-testing-in-ios/lessons/1',
        'info_dict': {
            'id': '248377018',
            'ext': 'mp4',
            'title': 'Testing In iOS Episode 1: Introduction',
            'duration': 133,
            'uploader': 'Ray Wenderlich',
            'uploader_id': 'user3304672',
        },
        'params': {
            'noplaylist': True,
            'skip_download': True,
        },
        'add_ie': [VimeoIE.ie_key()],
        'expected_warnings': ['HTTP Error 403: Forbidden'],
    }, {
        'url': 'https://videos.raywenderlich.com/courses/105-testing-in-ios/lessons/1',
        'info_dict': {
            'title': 'Testing in iOS',
            'id': '105-testing-in-ios',
        },
        'params': {
            'noplaylist': False,
        },
        'playlist_count': 29,
    }]

    def _real_extract(self, url):
        url, smuggled_data = unsmuggle_url(url, {})

        mobj = re.match(self._VALID_URL, url)
        course_id, lesson_id = mobj.group('course_id', 'id')
        video_id = '%s/%s' % (course_id, lesson_id)

        webpage = self._download_webpage(url, video_id)

        no_playlist = self._downloader.params.get('noplaylist')
        if no_playlist or smuggled_data.get('force_video', False):
            if no_playlist:
                self.to_screen(
                    'Downloading just video %s because of --no-playlist'
                    % video_id)
            if '>Subscribe to unlock' in webpage:
                raise ExtractorError(
                    'This content is only available for subscribers',
                    expected=True)
            vimeo_id = self._search_regex(
                r'data-vimeo-id=["\'](\d+)', webpage, 'video id')
            return self.url_result(
                VimeoIE._smuggle_referrer(
                    'https://player.vimeo.com/video/%s' % vimeo_id, url),
                ie=VimeoIE.ie_key(), video_id=vimeo_id)

        self.to_screen(
            'Downloading playlist %s - add --no-playlist to just download video'
            % course_id)

        lesson_ids = set((lesson_id, ))
        for lesson in re.findall(
                r'(<a[^>]+\bclass=["\']lesson-link[^>]+>)', webpage):
            attrs = extract_attributes(lesson)
            if not attrs:
                continue
            lesson_url = attrs.get('href')
            if not lesson_url:
                continue
            lesson_id = self._search_regex(
                r'/lessons/(\d+)', lesson_url, 'lesson id', default=None)
            if not lesson_id:
                continue
            lesson_ids.add(lesson_id)

        entries = []
        for lesson_id in sorted(lesson_ids):
            entries.append(self.url_result(
                smuggle_url(urljoin(url, lesson_id), {'force_video': True}),
                ie=RayWenderlichIE.ie_key()))

        title = self._search_regex(
            r'class=["\']course-title[^>]+>([^<]+)', webpage, 'course title',
            default=None)

        return self.playlist_result(entries, course_id, title)
