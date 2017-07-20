# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import (
    int_or_none,
    try_get,
    unified_timestamp,
)


class EggheadCourseIE(InfoExtractor):
    IE_DESC = 'egghead.io course'
    IE_NAME = 'egghead:course'
    _VALID_URL = r'https://egghead\.io/courses/(?P<id>[^/?#&]+)'
    _TEST = {
        'url': 'https://egghead.io/courses/professor-frisby-introduces-composable-functional-javascript',
        'playlist_count': 29,
        'info_dict': {
            'id': 'professor-frisby-introduces-composable-functional-javascript',
            'title': 'Professor Frisby Introduces Composable Functional JavaScript',
            'description': 're:(?s)^This course teaches the ubiquitous.*You\'ll start composing functionality before you know it.$',
        },
    }

    def _real_extract(self, url):
        playlist_id = self._match_id(url)

        course = self._download_json(
            'https://egghead.io/api/v1/series/%s' % playlist_id, playlist_id)

        entries = [
            self.url_result(
                'wistia:%s' % lesson['wistia_id'], ie='Wistia',
                video_id=lesson['wistia_id'], video_title=lesson.get('title'))
            for lesson in course['lessons'] if lesson.get('wistia_id')]

        return self.playlist_result(
            entries, playlist_id, course.get('title'),
            course.get('description'))


class EggheadLessonIE(InfoExtractor):
    IE_DESC = 'egghead.io lesson'
    IE_NAME = 'egghead:lesson'
    _VALID_URL = r'https://egghead\.io/lessons/(?P<id>[^/?#&]+)'
    _TEST = {
        'url': 'https://egghead.io/lessons/javascript-linear-data-flow-with-container-style-types-box',
        'info_dict': {
            'id': 'fv5yotjxcg',
            'ext': 'mp4',
            'title': 'Create linear data flow with container style types (Box)',
            'description': 'md5:9aa2cdb6f9878ed4c39ec09e85a8150e',
            'thumbnail': r're:^https?:.*\.jpg$',
            'timestamp': 1481296768,
            'upload_date': '20161209',
            'duration': 304,
            'view_count': 0,
            'tags': ['javascript', 'free'],
        },
        'params': {
            'skip_download': True,
        },
    }

    def _real_extract(self, url):
        lesson_id = self._match_id(url)

        lesson = self._download_json(
            'https://egghead.io/api/v1/lessons/%s' % lesson_id, lesson_id)

        return {
            '_type': 'url_transparent',
            'ie_key': 'Wistia',
            'url': 'wistia:%s' % lesson['wistia_id'],
            'id': lesson['wistia_id'],
            'title': lesson.get('title'),
            'description': lesson.get('summary'),
            'thumbnail': lesson.get('thumb_nail'),
            'timestamp': unified_timestamp(lesson.get('published_at')),
            'duration': int_or_none(lesson.get('duration')),
            'view_count': int_or_none(lesson.get('plays_count')),
            'tags': try_get(lesson, lambda x: x['tag_list'], list),
        }
