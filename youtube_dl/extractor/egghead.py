# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor


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
