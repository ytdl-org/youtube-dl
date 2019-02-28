from __future__ import unicode_literals

import json
import re

from .common import InfoExtractor
from ..compat import (
    compat_str,
    compat_HTTPError,
)
from ..utils import (
    clean_html,
    ExtractorError,
    remove_end,
    strip_or_none,
    unified_timestamp,
    urljoin,
)


class PacktPubBaseIE(InfoExtractor):
    _PACKT_BASE = 'https://www.packtpub.com'
    _MAPT_REST = '%s/mapt-rest' % _PACKT_BASE


class PacktPubIE(PacktPubBaseIE):
    _VALID_URL = r'https?://(?:(?:www\.)?packtpub\.com/mapt|subscription\.packtpub\.com)/video/[^/]+/(?P<course_id>\d+)/(?P<chapter_id>\d+)/(?P<id>\d+)'

    _TESTS = [{
        'url': 'https://www.packtpub.com/mapt/video/web-development/9781787122215/20528/20530/Project+Intro',
        'md5': '1e74bd6cfd45d7d07666f4684ef58f70',
        'info_dict': {
            'id': '20530',
            'ext': 'mp4',
            'title': 'Project Intro',
            'thumbnail': r're:(?i)^https?://.*\.jpg',
            'timestamp': 1490918400,
            'upload_date': '20170331',
        },
    }, {
        'url': 'https://subscription.packtpub.com/video/web_development/9781787122215/20528/20530/project-intro',
        'only_matching': True,
    }]
    _NETRC_MACHINE = 'packtpub'
    _TOKEN = None

    def _real_initialize(self):
        username, password = self._get_login_info()
        if username is None:
            return
        try:
            self._TOKEN = self._download_json(
                self._MAPT_REST + '/users/tokens', None,
                'Downloading Authorization Token', data=json.dumps({
                    'email': username,
                    'password': password,
                }).encode())['data']['access']
        except ExtractorError as e:
            if isinstance(e.cause, compat_HTTPError) and e.cause.code in (400, 401, 404):
                message = self._parse_json(e.cause.read().decode(), None)['message']
                raise ExtractorError(message, expected=True)
            raise

    def _handle_error(self, response):
        if response.get('status') != 'success':
            raise ExtractorError(
                '% said: %s' % (self.IE_NAME, response['message']),
                expected=True)

    def _download_json(self, *args, **kwargs):
        response = super(PacktPubIE, self)._download_json(*args, **kwargs)
        self._handle_error(response)
        return response

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        course_id, chapter_id, video_id = mobj.group(
            'course_id', 'chapter_id', 'id')

        headers = {}
        if self._TOKEN:
            headers['Authorization'] = 'Bearer ' + self._TOKEN
        video = self._download_json(
            '%s/users/me/products/%s/chapters/%s/sections/%s'
            % (self._MAPT_REST, course_id, chapter_id, video_id), video_id,
            'Downloading JSON video', headers=headers)['data']

        content = video.get('content')
        if not content:
            self.raise_login_required('This video is locked')

        video_url = content['file']

        metadata = self._download_json(
            '%s/products/%s/chapters/%s/sections/%s/metadata'
            % (self._MAPT_REST, course_id, chapter_id, video_id),
            video_id)['data']

        title = metadata['pageTitle']
        course_title = metadata.get('title')
        if course_title:
            title = remove_end(title, ' - %s' % course_title)
        timestamp = unified_timestamp(metadata.get('publicationDate'))
        thumbnail = urljoin(self._PACKT_BASE, metadata.get('filepath'))

        return {
            'id': video_id,
            'url': video_url,
            'title': title,
            'thumbnail': thumbnail,
            'timestamp': timestamp,
        }


class PacktPubCourseIE(PacktPubBaseIE):
    _VALID_URL = r'(?P<url>https?://(?:(?:www\.)?packtpub\.com/mapt|subscription\.packtpub\.com)/video/[^/]+/(?P<id>\d+))'
    _TESTS = [{
        'url': 'https://www.packtpub.com/mapt/video/web-development/9781787122215',
        'info_dict': {
            'id': '9781787122215',
            'title': 'Learn Nodejs by building 12 projects [Video]',
        },
        'playlist_count': 90,
    }, {
        'url': 'https://subscription.packtpub.com/video/web_development/9781787122215',
        'only_matching': True,
    }]

    @classmethod
    def suitable(cls, url):
        return False if PacktPubIE.suitable(url) else super(
            PacktPubCourseIE, cls).suitable(url)

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        url, course_id = mobj.group('url', 'id')

        course = self._download_json(
            '%s/products/%s/metadata' % (self._MAPT_REST, course_id),
            course_id)['data']

        entries = []
        for chapter_num, chapter in enumerate(course['tableOfContents'], 1):
            if chapter.get('type') != 'chapter':
                continue
            children = chapter.get('children')
            if not isinstance(children, list):
                continue
            chapter_info = {
                'chapter': chapter.get('title'),
                'chapter_number': chapter_num,
                'chapter_id': chapter.get('id'),
            }
            for section in children:
                if section.get('type') != 'section':
                    continue
                section_url = section.get('seoUrl')
                if not isinstance(section_url, compat_str):
                    continue
                entry = {
                    '_type': 'url_transparent',
                    'url': urljoin(url + '/', section_url),
                    'title': strip_or_none(section.get('title')),
                    'description': clean_html(section.get('summary')),
                    'ie_key': PacktPubIE.ie_key(),
                }
                entry.update(chapter_info)
                entries.append(entry)

        return self.playlist_result(entries, course_id, course.get('title'))
