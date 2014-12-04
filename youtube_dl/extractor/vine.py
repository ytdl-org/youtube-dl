from __future__ import unicode_literals

import re
import json
import itertools

from .common import InfoExtractor
from ..utils import unified_strdate


class VineIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?vine\.co/v/(?P<id>\w+)'
    _TEST = {
        'url': 'https://vine.co/v/b9KOOWX7HUx',
        'md5': '2f36fed6235b16da96ce9b4dc890940d',
        'info_dict': {
            'id': 'b9KOOWX7HUx',
            'ext': 'mp4',
            'title': 'Chicken.',
            'description': 'Chicken.',
            'upload_date': '20130519',
            'uploader': 'Jack Dorsey',
            'uploader_id': '76',
        },
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')

        webpage = self._download_webpage('https://vine.co/v/' + video_id, video_id)

        data = json.loads(self._html_search_regex(
            r'window\.POST_DATA = { %s: ({.+?}) }' % video_id, webpage, 'vine data'))

        formats = [
            {
                'url': data['videoLowURL'],
                'ext': 'mp4',
                'format_id': 'low',
            },
            {
                'url': data['videoUrl'],
                'ext': 'mp4',
                'format_id': 'standard',
            }
        ]

        return {
            'id': video_id,
            'title': self._og_search_title(webpage),
            'description': data['description'],
            'thumbnail': data['thumbnailUrl'],
            'upload_date': unified_strdate(data['created']),
            'uploader': data['username'],
            'uploader_id': data['userIdStr'],
            'like_count': data['likes']['count'],
            'comment_count': data['comments']['count'],
            'repost_count': data['reposts']['count'],
            'formats': formats,
        }


class VineUserIE(InfoExtractor):
    IE_NAME = 'vine:user'
    _VALID_URL = r'(?:https?://)?vine\.co/(?P<u>u/)?(?P<user>[^/]+)/?(\?.*)?$'
    _VINE_BASE_URL = "https://vine.co/"
    _TESTS = [
        {
            'url': 'https://vine.co/Visa',
            'info_dict': {
                'id': 'Visa',
            },
            'playlist_mincount': 46,
        },
        {
            'url': 'https://vine.co/u/941705360593584128',
            'only_matching': True,
        },
    ]

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        user = mobj.group('user')
        u = mobj.group('u')

        profile_url = "%sapi/users/profiles/%s%s" % (
            self._VINE_BASE_URL, 'vanity/' if not u else '', user)
        profile_data = self._download_json(
            profile_url, user, note='Downloading user profile data')

        user_id = profile_data['data']['userId']
        timeline_data = []
        for pagenum in itertools.count(1):
            timeline_url = "%sapi/timelines/users/%s?page=%s&size=100" % (
                self._VINE_BASE_URL, user_id, pagenum)
            timeline_page = self._download_json(
                timeline_url, user, note='Downloading page %d' % pagenum)
            timeline_data.extend(timeline_page['data']['records'])
            if timeline_page['data']['nextPage'] is None:
                break

        entries = [
            self.url_result(e['permalinkUrl'], 'Vine') for e in timeline_data]
        return self.playlist_result(entries, user)
