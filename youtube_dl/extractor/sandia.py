# coding: utf-8
from __future__ import unicode_literals

import json

from .common import InfoExtractor
from ..utils import (
    int_or_none,
    mimetype2ext,
)


class SandiaIE(InfoExtractor):
    IE_DESC = 'Sandia National Laboratories'
    _VALID_URL = r'https?://digitalops\.sandia\.gov/Mediasite/Play/(?P<id>[0-9a-f]+)'
    _TEST = {
        'url': 'http://digitalops.sandia.gov/Mediasite/Play/24aace4429fc450fb5b38cdbf424a66e1d',
        'md5': '9422edc9b9a60151727e4b6d8bef393d',
        'info_dict': {
            'id': '24aace4429fc450fb5b38cdbf424a66e1d',
            'ext': 'mp4',
            'title': 'Xyce Software Training - Section 1',
            'description': 're:(?s)SAND Number: SAND 2013-7800.{200,}',
            'upload_date': '20120409',
            'timestamp': 1333983600,
            'duration': 7794,
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)

        presentation_data = self._download_json(
            'http://digitalops.sandia.gov/Mediasite/PlayerService/PlayerService.svc/json/GetPlayerOptions',
            video_id, data=json.dumps({
                'getPlayerOptionsRequest': {
                    'ResourceId': video_id,
                    'QueryString': '',
                }
            }), headers={
                'Content-Type': 'application/json; charset=utf-8',
            })['d']['Presentation']

        title = presentation_data['Title']

        formats = []
        for stream in presentation_data.get('Streams', []):
            for fd in stream.get('VideoUrls', []):
                formats.append({
                    'format_id': fd['MediaType'],
                    'format_note': fd['MimeType'].partition('/')[2],
                    'ext': mimetype2ext(fd['MimeType']),
                    'url': fd['Location'],
                    'protocol': 'f4m' if fd['MimeType'] == 'video/x-mp4-fragmented' else None,
                })
        self._sort_formats(formats)

        return {
            'id': video_id,
            'title': title,
            'description': presentation_data.get('Description'),
            'formats': formats,
            'timestamp': int_or_none(presentation_data.get('UnixTime'), 1000),
            'duration': int_or_none(presentation_data.get('Duration'), 1000),
        }
