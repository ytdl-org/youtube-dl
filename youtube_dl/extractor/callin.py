# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor


class CallinIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?callin\.com/episode/(?P<id>[^/#?]+)'
    _TESTS = [{
        'url': 'https://www.callin.com/episode/fcc-commissioner-brendan-carr-on-elons-PrumRdSQJW',
        'md5': 'TODO: md5 sum of the first 10241 bytes of the video file (use --test)',
        'info_dict': {
            'id': '42',
            'ext': 'mp4',
            'title': 'FCC Commissioner Brendan Carr on Elon’s Starlink',
        }
    }, {
        'url': 'https://www.callin.com/episode/episode-81-elites-melt-down-over-student-debt-lzxMidUnjA',
        'md5': 'TODO: md5 sum of the first 10241 bytes of the video file (use --test)',
        'info_dict': {
            'id': '42',
            'ext': 'mp4',
            'title': 'Episode 81- Elites MELT DOWN over Student Debt Victory? Rumble in NYC?',
        }
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        # TODO more code goes here, for example ...
        title = self._html_search_regex(r'<h1>(.+?)</h1>', webpage, 'title')

        return {
            'id': video_id,
            'title': title,
            'description': self._og_search_description(webpage),
            'uploader': self._search_regex(r'<div[^>]+id="uploader"[^>]*>([^<]+)<', webpage, 'uploader', fatal=False),
            # TODO more properties (see youtube_dl/extractor/common.py)
        }