# coding: utf-8
from __future__ import unicode_literals
from .common import InfoExtractor
from ..utils import int_or_none


class VidliiIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?vidlii\.com/watch\?v\=(?P<id>[a-zA-Z0-9]+$)'
    _TEST = {
        'url': 'https://www.vidlii.com/watch?v=vBo2IcrwOkO',
        'md5': 'b42640a596b4dc986702567d49268963',
        'info_dict': {
            'id': 'vBo2IcrwOkO',
            'ext': 'mp4',
            'title': '(OLD VIDEO) i like youtube!!',

        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)
        video_url = self._search_regex(r'var videoInfo\s+=\s+{\s+src\:\s+"(.+?)"', webpage, 'video URL')
        title = self._html_search_regex(r'<h1>(.+?)</h1>', webpage, 'title')
        view_count = int_or_none(self._html_search_regex(r'<div[^>]+class="w_views"[^>]*><strong>(\d*)', webpage, 'views'))

        return {
            'id': video_id,
            'title': title,
            'view_count': view_count,
            'formats': [{
                'url': video_url,
            }],

        }
