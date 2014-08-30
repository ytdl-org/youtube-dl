# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import int_or_none

class AnySexIE(InfoExtractor):
    _VALID_URL = r'http?://(?:www\.)?anysex\.com/(?P<id>\d+)/?'
    _TEST = {
        'url': 'http://anysex.com/156592/',
        'md5': '023e9fbb7f7987f5529a394c34ad3d3d',
        'info_dict': {
            'id': '156592',
            'ext': 'mp4',
            'title': 'Busty and sexy blondie in her bikini strips for you',
            'duration': 270,
            'view_count': 3652
        }
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')

        webpage = self._download_webpage(url, video_id)
        title = self._html_search_regex(r'<title>(.*?)</title>', webpage, 'title')
        video_url = self._html_search_regex(r'video_url: \'(.*?)\',', webpage, 'video_url')
        thumbnail = self._html_search_regex(r'preview_url: \'(.*?)\',', webpage, 'thumbnail')

        mobj = re.search(r'<b>Duration:</b> (?P<minutes>\d+):(?P<seconds>\d+)<', webpage)
        duration = int(mobj.group('minutes')) * 60 + int(mobj.group('seconds')) if mobj else None

        view_count = self._html_search_regex(r'<b>Views:</b> (\d+)', webpage, 'view count', fatal=False)

        return {
            'id': video_id,
            'ext': 'mp4',
            'url': video_url,
            'title': title,
            'duration': duration,
            'view_count': int_or_none(view_count),
        }
