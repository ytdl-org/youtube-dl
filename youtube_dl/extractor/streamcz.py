# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import re
import json

from .common import InfoExtractor
from ..utils import (
    int_or_none,
    compat_str,
)


class StreamCZIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?stream\.cz/.+/(?P<videoid>.+)'

    _TESTS = [{
        'url': 'http://www.stream.cz/peklonataliri/765767-ecka-pro-deti',
        'md5': '6d3ca61a8d0633c9c542b92fcb936b0c',
        'info_dict': {
            'id': '765767',
            'ext': 'mp4',
            'title': 'Peklo na talíři: Éčka pro děti',
            'description': 'md5:49ace0df986e95e331d0fe239d421519',
            'thumbnail': 'http://im.stream.cz/episode/52961d7e19d423f8f06f0100',
            'duration': 256,
        },
    }, {
        'url': 'http://www.stream.cz/blanik/10002447-tri-roky-pro-mazanka',
        'md5': '246272e753e26bbace7fcd9deca0650c',
        'info_dict': {
            'id': '10002447',
            'ext': 'mp4',
            'title': 'Kancelář Blaník: Tři roky pro Mazánka',
            'description': 'md5:9177695a8b756a0a8ab160de4043b392',
            'thumbnail': 'http://im.stream.cz/episode/537f838c50c11f8d21320000',
            'duration': 368,
        },
    }]

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('videoid')

        webpage = self._download_webpage(url, video_id)

        data = self._html_search_regex(r'Stream\.Data\.Episode\((.+?)\);', webpage, 'stream data')

        jsonData = json.loads(data)

        formats = []
        for video in jsonData['instances']:
            for video_format in video['instances']:
                format_id = video_format['quality']

                if format_id == '240p':
                    quality = 0
                elif format_id == '360p':
                    quality = 1
                elif format_id == '480p':
                    quality = 2
                elif format_id == '720p':
                    quality = 3

                formats.append({
                    'format_id': '%s-%s' % (video_format['type'].split('/')[1], format_id),
                    'url': video_format['source'],
                    'quality': quality,
                })

        self._sort_formats(formats)

        return {
            'id': compat_str(jsonData['episode_id']),
            'title': self._og_search_title(webpage),
            'thumbnail': jsonData['episode_image_original_url'].replace('//', 'http://'),
            'formats': formats,
            'description': self._og_search_description(webpage),
            'duration': int_or_none(jsonData['duration']),
            'view_count': int_or_none(jsonData['stats_total']),
        }
