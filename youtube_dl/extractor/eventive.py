# coding: utf-8
from __future__ import unicode_literals
import re
from .common import InfoExtractor
from ..compat import (
    compat_etree_fromstring,
    compat_urllib_parse_unquote_plus,
)
from ..utils import (
    urlencode_postdata,
)

API_URL = 'https://api.eventive.org/watch/play'


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

        post = {
            "event_id": video_id,
            "film_id": "5f22387785a26f00360d29c9",
            "token": ""
        }
        video = self._download_json(API_URL, video_id=video_id, data=urlencode_postdata(post))

        formats = []
        for stream in video.get('playlist', []):
            formats.extend(self._extract_ism_formats(stream['url'], video_id))
        self._sort_formats(formats)

        info = {
            'id': video_id,
            'title': stream['name'],
            'formats': formats,
        }

        return info
