# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    determine_ext,
    js_to_json,
    parse_duration,
    remove_end,
)


class LRTIE(InfoExtractor):
    IE_NAME = 'lrt.lt'
    _VALID_URL = r'https?://(?:www\.)?lrt\.lt/mediateka/irasas/(?P<id>[0-9]+)'
    _TEST = {
        'url': 'http://www.lrt.lt/mediateka/irasas/54391/',
        'info_dict': {
            'id': '54391',
            'ext': 'mp4',
            'title': 'Septynios Kauno dienos',
            'description': 'md5:24d84534c7dc76581e59f5689462411a',
            'duration': 1783,
        },
        'params': {
            'skip_download': True,  # HLS download
        },
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        title = remove_end(self._og_search_title(webpage), ' - LRT')
        thumbnail = self._og_search_thumbnail(webpage)
        description = self._og_search_description(webpage)
        duration = parse_duration(self._search_regex(
            r"'duration':\s*'([^']+)',", webpage,
            'duration', fatal=False, default=None))

        formats = []
        for js in re.findall(r'(?s)config:\s*(\{.*?\})', webpage):
            data = self._parse_json(js, video_id, transform_source=js_to_json)
            if 'provider' not in data:
                continue
            if data['provider'] == 'rtmp':
                formats.append({
                    'format_id': 'rtmp',
                    'ext': determine_ext(data['file']),
                    'url': data['streamer'],
                    'play_path': 'mp4:%s' % data['file'],
                    'preference': -1,
                    'rtmp_real_time': True,
                })
            else:
                formats.extend(
                    self._extract_m3u8_formats(data['file'], video_id, 'mp4'))

        return {
            'id': video_id,
            'title': title,
            'formats': formats,
            'thumbnail': thumbnail,
            'description': description,
            'duration': duration,
        }
