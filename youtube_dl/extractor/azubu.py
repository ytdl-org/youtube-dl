from __future__ import unicode_literals

import json

from .common import InfoExtractor
from ..utils import float_or_none


class AzubuIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?azubu\.tv/[^/]+#!/play/(?P<id>\d+)'
    _TESTS = [
        {
            'url': 'http://www.azubu.tv/GSL#!/play/15575/2014-hot6-cup-last-big-match-ro8-day-1',
            'md5': 'a88b42fcf844f29ad6035054bd9ecaf4',
            'info_dict': {
                'id': '15575',
                'ext': 'mp4',
                'title': '2014 HOT6 CUP LAST BIG MATCH Ro8 Day 1',
                'description': 'md5:d06bdea27b8cc4388a90ad35b5c66c01',
                'thumbnail': 're:^https?://.*\.jpe?g',
                'timestamp': 1417523507.334,
                'upload_date': '20141202',
                'duration': 9988.7,
                'uploader': 'GSL',
                'uploader_id': 414310,
                'view_count': int,
            },
        },
        {
            'url': 'http://www.azubu.tv/FnaticTV#!/play/9344/-fnatic-at-worlds-2014:-toyz---%22i-love-rekkles,-he-has-amazing-mechanics%22-',
            'md5': 'b72a871fe1d9f70bd7673769cdb3b925',
            'info_dict': {
                'id': '9344',
                'ext': 'mp4',
                'title': 'Fnatic at Worlds 2014: Toyz - "I love Rekkles, he has amazing mechanics"',
                'description': 'md5:4a649737b5f6c8b5c5be543e88dc62af',
                'thumbnail': 're:^https?://.*\.jpe?g',
                'timestamp': 1410530893.320,
                'upload_date': '20140912',
                'duration': 172.385,
                'uploader': 'FnaticTV',
                'uploader_id': 272749,
                'view_count': int,
            },
        },
    ]

    def _real_extract(self, url):
        video_id = self._match_id(url)

        data = self._download_json(
            'http://www.azubu.tv/api/video/%s' % video_id, video_id)['data']

        title = data['title'].strip()
        description = data['description']
        thumbnail = data['thumbnail']
        view_count = data['view_count']
        uploader = data['user']['username']
        uploader_id = data['user']['id']

        stream_params = json.loads(data['stream_params'])

        timestamp = float_or_none(stream_params['creationDate'], 1000)
        duration = float_or_none(stream_params['length'], 1000)

        renditions = stream_params.get('renditions') or []
        video = stream_params.get('FLVFullLength') or stream_params.get('videoFullLength')
        if video:
            renditions.append(video)

        formats = [{
            'url': fmt['url'],
            'width': fmt['frameWidth'],
            'height': fmt['frameHeight'],
            'vbr': float_or_none(fmt['encodingRate'], 1000),
            'filesize': fmt['size'],
            'vcodec': fmt['videoCodec'],
            'container': fmt['videoContainer'],
        } for fmt in renditions if fmt['url']]
        self._sort_formats(formats)

        return {
            'id': video_id,
            'title': title,
            'description': description,
            'thumbnail': thumbnail,
            'timestamp': timestamp,
            'duration': duration,
            'uploader': uploader,
            'uploader_id': uploader_id,
            'view_count': view_count,
            'formats': formats,
        }
