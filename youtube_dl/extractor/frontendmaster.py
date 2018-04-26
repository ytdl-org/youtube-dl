# coding: utf-8
from __future__ import unicode_literals

import json
import re

from youtube_dl.utils import try_get
from .common import InfoExtractor
from ..compat import (
    # compat_str,
    compat_urlparse,
    compat_str)

class FrontEndMasterBaseIE(InfoExtractor):
    _API_BASE = 'https://api.frontendmasters.com/v1/kabuki/courses'

    _supported_resolutions = {
        'low': 360,
        'mid': 720,
        'high': 1080
    }

    _supported_formats = ['mp4', 'webm']

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


class FrontEndMasterIE(FrontEndMasterBaseIE):
    _VALID_URL = r'https?://(?:www\.)?frontendmasters\.com/courses/(?P<courseid>[a-z\-]+)/(?P<id>[a-z\-]+)/?'
    _TEST = {
        'url': 'https://frontendmasters.com/courses/content-strategy/introduction/',
        'md5': 'TODO: md5 sum of the first 10241 bytes of the video file (use --test)',
        'info_dict': {
            'id': 'introduction',
            'courseid': 'content-strategy',
            'ext': 'webm',
            'title': 'Introduction',
            'thumbnail': r're:^https?://.*\.jpg$',
            # TODO more properties, either as:
            # * A value
            # * MD5 checksum; start the string with md5:
            # * A regular expression; start the string with re:
            # * Any Python type (for example int or float)
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        course_id = self._match_course_id(url)
        json_content = self._download_course(course_id=course_id, url=url, display_id=None)
        webpage = self._download_webpage(url, video_id)

        # TODO more code goes here, for example ...
        lesson_index = json_content['lessonSlugs'].index(video_id)
        lesson_hash = json_content['lessonHashes'][lesson_index]
        lesson_data = json_content['lessonData'][lesson_hash]
        lesson_source_base = lesson_data['sourceBase']

        video_url_request = "%s/source?r=360&f=mp4"


        title = lesson_data['title']
        description = json_content['description']

        # title = self._html_search_regex(r'<div class="title">(.+?)</div>', webpage, 'title')

        return {
            'id': video_id,
            'title': title,
            'description': description,

            # TODO more properties (see youtube_dl/extractor/common.py)
        }