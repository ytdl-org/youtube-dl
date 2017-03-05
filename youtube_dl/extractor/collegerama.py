from __future__ import unicode_literals

import json

from .common import InfoExtractor
from ..utils import (
    float_or_none,
    int_or_none,
    sanitized_Request,
)


class CollegeRamaIE(InfoExtractor):
    _VALID_URL = r'https?://collegerama\.tudelft\.nl/Mediasite/Play/(?P<id>[\da-f]+)'
    _TESTS = [
        {
            'url': 'https://collegerama.tudelft.nl/Mediasite/Play/585a43626e544bdd97aeb71a0ec907a01d',
            'md5': '481fda1c11f67588c0d9d8fbdced4e39',
            'info_dict': {
                'id': '585a43626e544bdd97aeb71a0ec907a01d',
                'ext': 'mp4',
                'title': 'Een nieuwe wereld: waarden, bewustzijn en techniek van de mensheid 2.0.',
                'description': '',
                'thumbnail': r're:^https?://.*\.jpg$',
                'duration': 7713.088,
                'timestamp': 1413309600,
                'upload_date': '20141014',
            },
        },
        {
            'url': 'https://collegerama.tudelft.nl/Mediasite/Play/86a9ea9f53e149079fbdb4202b521ed21d?catalog=fd32fd35-6c99-466c-89d4-cd3c431bc8a4',
            'md5': 'ef1fdded95bdf19b12c5999949419c92',
            'info_dict': {
                'id': '86a9ea9f53e149079fbdb4202b521ed21d',
                'ext': 'wmv',
                'title': '64ste Vakantiecursus: Afvalwater',
                'description': 'md5:7fd774865cc69d972f542b157c328305',
                'duration': 10853,
                'timestamp': 1326446400,
                'upload_date': '20120113',
            },
        },
    ]

    def _real_extract(self, url):
        video_id = self._match_id(url)

        player_options_request = {
            'getPlayerOptionsRequest': {
                'ResourceId': video_id,
                'QueryString': '',
            }
        }

        request = sanitized_Request(
            'http://collegerama.tudelft.nl/Mediasite/PlayerService/PlayerService.svc/json/GetPlayerOptions',
            json.dumps(player_options_request))
        request.add_header('Content-Type', 'application/json')

        player_options = self._download_json(request, video_id)

        presentation = player_options['d']['Presentation']
        title = presentation['Title']
        description = presentation.get('Description')
        thumbnail = None
        duration = float_or_none(presentation.get('Duration'), 1000)
        timestamp = int_or_none(presentation.get('UnixTime'), 1000)

        formats = []
        for stream in presentation['Streams']:
            for video in stream['VideoUrls']:
                thumbnail_url = stream.get('ThumbnailUrl')
                if thumbnail_url:
                    thumbnail = 'http://collegerama.tudelft.nl' + thumbnail_url
                format_id = video['MediaType']
                if format_id == 'SS':
                    continue
                formats.append({
                    'url': video['Location'],
                    'format_id': format_id,
                })
        self._sort_formats(formats)

        return {
            'id': video_id,
            'title': title,
            'description': description,
            'thumbnail': thumbnail,
            'duration': duration,
            'timestamp': timestamp,
            'formats': formats,
        }
