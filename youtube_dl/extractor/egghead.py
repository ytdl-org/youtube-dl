# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor


class EggheadCourseIE(InfoExtractor):
    IE_DESC = 'egghead.io course'
    IE_NAME = 'egghead:course'
    _VALID_URL = r'https://egghead\.io/courses/(?P<id>[a-zA-Z_0-9-]+)'
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
        api_url = 'https://egghead.io/api/v1/series/' + playlist_id
        course = self._download_json(api_url, playlist_id)
        title = course.get('title')
        description = course.get('description')

        lessons = course.get('lessons')
        entries = [{'_type': 'url', 'ie_key': 'Wistia', 'url': 'wistia:' + l.get('wistia_id')} for l in lessons]

        return {
            '_type': 'playlist',
            'id': playlist_id,
            'title': title,
            'description': description,
            'entries': entries,
        }
