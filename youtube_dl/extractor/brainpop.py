# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor


class BrainPOPIE(InfoExtractor):
    _VALID_URL = r'https?:\/\/(?:(.+)\.)?brainpop\.com\/(?P<id>[^\r\n]+)'
    _TEST = {
        'url': 'https://www.brainpop.com/english/freemovies/williamshakespeare/',
        'md5': '676d936271b628dc05e4cec377751919',
        'info_dict': {
            'id': 'english/freemovies/williamshakespeare/',
            'ext': 'mp4',
            'title': 'William Shakespeare - BrainPOP',
            'thumbnail': 're:^https?://.*\.png$',
            'description': 'He could do comedies, tragedies, histories and poetry.  Learn about the greatest playwright in the history of the English language!',
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        self.report_extraction(video_id)

        ec_token = self._html_search_regex(r'ec_token : \'(.+)\'', webpage, 'token')
        movie_cdn_path = self._html_search_regex(r'movie_cdn_path : \'(.+)\'', webpage, 'cdn path')
        mp4 = self._html_search_regex(r'mp4":"([^"]*)', webpage, 'mp4')

        url = movie_cdn_path + mp4.replace('\\', '') + '?' + ec_token

        title = self._html_search_regex(r'type":"Movie","name":"([^"]*)"', webpage, 'title') or self._html_search_regex(r'<title>(.+?)</title>', webpage, 'title')

        thumbnail_cdn = self._html_search_regex(r"'cdn_path' : '([^']*)'", webpage, 'thumbnail cdn', fatal=False)
        thumbnail_image = self._html_search_regex(r'type":"Movie","name":"[^"]*","image":"([^"]*)"', webpage, 'thumbnail', fatal=False)
        thumbnail = thumbnail_cdn + thumbnail_image.replace('\\', '')

        description = self._html_search_regex(r'type":"Movie","name":"[^"]*","image":"[^"]*","description":"([^"]*)"', webpage, 'description', fatal=False)

        return {
            'id': video_id,
            'url': url,
            'title': title,
            'thumbnail': thumbnail,
            'description': description,
        }
