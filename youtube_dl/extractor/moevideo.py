# coding: utf-8
from __future__ import unicode_literals

import json
import re

from .common import InfoExtractor
from ..compat import compat_urllib_parse
from ..utils import (
    ExtractorError,
    int_or_none,
    sanitized_Request,
)


class MoeVideoIE(InfoExtractor):
    IE_DESC = 'LetitBit video services: moevideo.net, playreplay.net and videochart.net'
    _VALID_URL = r'''(?x)
        https?://(?P<host>(?:www\.)?
        (?:(?:moevideo|playreplay|videochart)\.net))/
        (?:video|framevideo)/(?P<id>[0-9]+\.[0-9A-Za-z]+)'''
    _API_URL = 'http://api.letitbit.net/'
    _API_KEY = 'tVL0gjqo5'
    _TESTS = [
        {
            'url': 'http://moevideo.net/video/00297.0036103fe3d513ef27915216fd29',
            'md5': '129f5ae1f6585d0e9bb4f38e774ffb3a',
            'info_dict': {
                'id': '00297.0036103fe3d513ef27915216fd29',
                'ext': 'flv',
                'title': 'Sink cut out machine',
                'description': 'md5:f29ff97b663aefa760bf7ca63c8ca8a8',
                'thumbnail': 're:^https?://.*\.jpg$',
                'width': 540,
                'height': 360,
                'duration': 179,
                'filesize': 17822500,
            }
        },
        {
            'url': 'http://playreplay.net/video/77107.7f325710a627383d40540d8e991a',
            'md5': '74f0a014d5b661f0f0e2361300d1620e',
            'info_dict': {
                'id': '77107.7f325710a627383d40540d8e991a',
                'ext': 'flv',
                'title': 'Operacion Condor.',
                'description': 'md5:7e68cb2fcda66833d5081c542491a9a3',
                'thumbnail': 're:^https?://.*\.jpg$',
                'width': 480,
                'height': 296,
                'duration': 6027,
                'filesize': 588257923,
            },
            'skip': 'Video has been removed',
        },
    ]

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')

        webpage = self._download_webpage(
            'http://%s/video/%s' % (mobj.group('host'), video_id),
            video_id, 'Downloading webpage')

        title = self._og_search_title(webpage)
        thumbnail = self._og_search_thumbnail(webpage)
        description = self._og_search_description(webpage)

        r = [
            self._API_KEY,
            [
                'preview/flv_link',
                {
                    'uid': video_id,
                },
            ],
        ]
        r_json = json.dumps(r)
        post = compat_urllib_parse.urlencode({'r': r_json})
        req = sanitized_Request(self._API_URL, post)
        req.add_header('Content-type', 'application/x-www-form-urlencoded')

        response = self._download_json(req, video_id)
        if response['status'] != 'OK':
            raise ExtractorError(
                '%s returned error: %s' % (self.IE_NAME, response['data']),
                expected=True
            )
        item = response['data'][0]
        video_url = item['link']
        duration = int_or_none(item['length'])
        width = int_or_none(item['width'])
        height = int_or_none(item['height'])
        filesize = int_or_none(item['convert_size'])

        formats = [{
            'format_id': 'sd',
            'http_headers': {'Range': 'bytes=0-'},  # Required to download
            'url': video_url,
            'width': width,
            'height': height,
            'filesize': filesize,
        }]

        return {
            'id': video_id,
            'title': title,
            'thumbnail': thumbnail,
            'description': description,
            'duration': duration,
            'formats': formats,
        }
