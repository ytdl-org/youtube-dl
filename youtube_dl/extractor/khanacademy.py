from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    unified_strdate,
)


class KhanAcademyIE(InfoExtractor):
    _VALID_URL = r'^https?://(?:(?:www|api)\.)?khanacademy\.org/(?P<key>[^/]+)/(?:[^/]+/){,2}(?P<id>[^?#/]+)(?:$|[?#])'
    IE_NAME = 'KhanAcademy'

    _TESTS = [{
        'url': 'http://www.khanacademy.org/video/one-time-pad',
        'md5': '7b391cce85e758fb94f763ddc1bbb979',
        'info_dict': {
            'id': 'one-time-pad',
            'ext': 'webm',
            'title': 'The one-time pad',
            'description': 'The perfect cipher',
            'duration': 176,
            'uploader': 'Brit Cruise',
            'uploader_id': 'khanacademy',
            'upload_date': '20120411',
        },
        'add_ie': ['Youtube'],
    }, {
        'url': 'https://www.khanacademy.org/math/applied-math/cryptography',
        'info_dict': {
            'id': 'cryptography',
            'title': 'Journey into cryptography',
            'description': 'How have humans protected their secret messages through history? What has changed today?',
        },
        'playlist_mincount': 3,
    }]

    def _real_extract(self, url):
        m = re.match(self._VALID_URL, url)
        video_id = m.group('id')

        if m.group('key') == 'video':
            data = self._download_json(
                'http://api.khanacademy.org/api/v1/videos/' + video_id,
                video_id, 'Downloading video info')

            upload_date = unified_strdate(data['date_added'])
            uploader = ', '.join(data['author_names'])
            return {
                '_type': 'url_transparent',
                'url': data['url'],
                'id': video_id,
                'title': data['title'],
                'thumbnail': data['image_url'],
                'duration': data['duration'],
                'description': data['description'],
                'uploader': uploader,
                'upload_date': upload_date,
            }
        else:
            # topic
            data = self._download_json(
                'http://api.khanacademy.org/api/v1/topic/' + video_id,
                video_id, 'Downloading topic info')

            entries = [
                {
                    '_type': 'url',
                    'url': c['url'],
                    'id': c['id'],
                    'title': c['title'],
                }
                for c in data['children'] if c['kind'] in ('Video', 'Topic')]

            return {
                '_type': 'playlist',
                'id': video_id,
                'title': data['title'],
                'description': data['description'],
                'entries': entries,
            }
