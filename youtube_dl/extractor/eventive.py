# coding: utf-8
from __future__ import unicode_literals
import re
from .common import InfoExtractor

class EventiveIE(InfoExtractor):
    SUBTITLE_DATE_RE = re.compile(r'\((\d{2}\.\d{2}\.\d{4}\s\d{2}:\d{2})\)$')

    _VALID_URL = r'https://watch\.eventive\.org/account/play/(?P<id>[a-f\d+]{24})(?:\?m=1)?'
    _TESTS = [
        {
            'note': 'Test Url from issue: https://github.com/ytdl-org/youtube-dl/issues/26619',
            'url': 'https://watch.eventive.org/account/play/5f0368a74282a70029055ca8',
            'md5': '',
            'info_dict': {
                'id': '5f0368a74282a70029055ca8',
                'ext': 'mp4',
                'title': 'TEST YOUR DEVICE COMPATIBILITY',
                'thumbnail': r're:https://eventive.imgix.net/.*\.jpg$',
            }
        },
    ]

    def _real_extract(self, url):
        video_id = self._match_id(url)

        info = {
            'id': video_id,
        }
        return info
