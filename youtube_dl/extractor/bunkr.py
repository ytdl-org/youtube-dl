# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor


class BunkrExtractor(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?media-files.bunkr\.ru/(?P<id>[0-9]+)'
    _TEST = {
        'url': ' https://media-files.bunkr.ru/miera2000-(18)-xXmlmXQU.mp4',
        'md5': 'TODO: md5 sum of the first 10241 bytes of the video file (use --test)',
        'info_dict': {
            'id': '42',
            'ext': 'mp4',
            'title': 'miera2000-(18)-xXmlmXQU',
            'thumbnail': r're:^https?://.*\.jpg$',
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        title = self._html_search_regex(r'<h1>(.+?)</h1>', webpage, 'title')
        return {
            'id': video_id,
            'title': title,
            'description': self._og_search_description(webpage),
            'uploader': self._search_regex(r'<div[^>]+id="uploader"[^>]*>([^<]+)<', webpage, 'uploader', fatal=False),
        }