# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    parse_duration,
    sanitized_Request,
    urlencode_postdata,
)


class ShareSixIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?sharesix\.com/(?:f/)?(?P<id>[0-9a-zA-Z]+)'
    _TESTS = [
        {
            'url': 'http://sharesix.com/f/OXjQ7Y6',
            'md5': '9e8e95d8823942815a7d7c773110cc93',
            'info_dict': {
                'id': 'OXjQ7Y6',
                'ext': 'mp4',
                'title': 'big_buck_bunny_480p_surround-fix.avi',
                'duration': 596,
                'width': 854,
                'height': 480,
            },
        },
        {
            'url': 'http://sharesix.com/lfrwoxp35zdd',
            'md5': 'dd19f1435b7cec2d7912c64beeee8185',
            'info_dict': {
                'id': 'lfrwoxp35zdd',
                'ext': 'flv',
                'title': 'WhiteBoard___a_Mac_vs_PC_Parody_Cartoon.mp4.flv',
                'duration': 65,
                'width': 1280,
                'height': 720,
            },
        }
    ]

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')

        fields = {
            'method_free': 'Free'
        }
        post = urlencode_postdata(fields)
        req = sanitized_Request(url, post)
        req.add_header('Content-type', 'application/x-www-form-urlencoded')

        webpage = self._download_webpage(req, video_id,
                                         'Downloading video page')

        video_url = self._search_regex(
            r"var\slnk1\s=\s'([^']+)'", webpage, 'video URL')
        title = self._html_search_regex(
            r'(?s)<dt>Filename:</dt>.+?<dd>(.+?)</dd>', webpage, 'title')
        duration = parse_duration(
            self._search_regex(
                r'(?s)<dt>Length:</dt>.+?<dd>(.+?)</dd>',
                webpage,
                'duration',
                fatal=False
            )
        )

        m = re.search(
            r'''(?xs)<dt>Width\sx\sHeight</dt>.+?
                     <dd>(?P<width>\d+)\sx\s(?P<height>\d+)</dd>''',
            webpage
        )
        width = height = None
        if m:
            width, height = int(m.group('width')), int(m.group('height'))

        formats = [{
            'format_id': 'sd',
            'url': video_url,
            'width': width,
            'height': height,
        }]

        return {
            'id': video_id,
            'title': title,
            'duration': duration,
            'formats': formats,
        }
