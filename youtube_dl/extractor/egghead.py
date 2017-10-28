# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import (
    int_or_none,
    try_get,
    unified_timestamp,
)


class EggheadShared():
    def extract_lesson_metadata(self, lesson):
        info = {
            'title': lesson.get('title'),
            'description': lesson.get('summary'),
            'thumbnail': lesson.get('thumb_nail'),
            'timestamp': unified_timestamp(lesson.get('published_at')),
            'duration': int_or_none(lesson.get('duration')),
            'view_count': int_or_none(lesson.get('plays_count')),
            'tags': try_get(lesson, lambda x: x['tag_list'], list),
        }

        def find_id_and_dlurl():
            vid_id = lesson.get('wistia_id')
            if vid_id:
                return {'ie_key': 'Wistia', '_type': 'url_transparent',
                        'id': vid_id, 'url': 'wistia:' + vid_id}

            self.report_warning('Cannot find an proper ID, will use lesson name URL slug')
            vid_id = self._html_search_regex(
                r'^https?://egghead\.io/lessons/([A-Za-z0-9][A-Za-z0-9-]*)$',
                lesson.get('http_url'),
                'lesson name URL part as ID of last resort',
                group=1)

            mu = lesson.get('media_urls')
            if mu:
                src = mu.get('dash_url')
                if src:
                    return {'id': vid_id, 'formats': self._extract_mpd_formats(src, vid_id)}
                src = mu.get('hls_url')
                if src:
                    return {'id': vid_id, 'formats': self._extract_m3u8_formats(src, vid_id, entry_protocol='m3u8_native', m3u8_id='hls')}
            raise NotImplementedError('Unable to detect download URL')
        info.update(find_id_and_dlurl())

        return info


class EggheadCourseIE(InfoExtractor, EggheadShared):
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
            'https://egghead.io/api/v1/series/' + playlist_id, playlist_id)
        entries = [self.extract_lesson_metadata(lesson)
                   for lesson in course['lessons']]
        return self.playlist_result(
            entries, playlist_id, course.get('title'),
            course.get('description'))


class EggheadLessonIE(InfoExtractor, EggheadShared):
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
            'https://egghead.io/api/v1/lessons/' + lesson_id, lesson_id)
        return self.extract_lesson_metadata(lesson)
