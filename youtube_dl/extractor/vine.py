from __future__ import unicode_literals

import re
import json

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