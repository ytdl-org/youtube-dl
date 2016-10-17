# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor


class LearnrIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?learnr\.pro/view/video/(?P<id>[0-9]+)'
    _TEST = {
        'url': 'http://www.learnr.pro/view/video/51624-web-development-tutorial-for-beginners-1-how-to-build-webpages-with-html-css-javascript',
        'md5': '3719fdf0a68397f49899e82c308a89de',
        'info_dict': {
            'id': '51624',
            'ext': 'mp4',
            'title': 'Web Development Tutorial for Beginners (#1) - How to build webpages with HTML, CSS, Javascript',
            'description': 'md5:b36dbfa92350176cdf12b4d388485503',
            'uploader': 'LearnCode.academy',
            'uploader_id': 'learncodeacademy',
            'upload_date': '20131021',
        },
        'add_ie': ['Youtube'],
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        return {
            '_type': 'url_transparent',
            'url': self._search_regex(
                r"videoId\s*:\s*'([^']+)'", webpage, 'youtube id'),
            'id': video_id,
        }
