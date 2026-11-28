# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor


class NestIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?video.nest\.com/clip/(?P<id>)(.mp4)?'
    _TEST = {
        'url': 'https://video.nest.com/clip/73ddb6bd57c4485597a76e154a4429ea.mp4',
        'md5': '7ab4eb6d4c2480be1740cc014a76ee96',
        'info_dict': {
            'id': '73ddb6bd57c4485597a76e154a4429ea',
            'ext': 'mp4',
            'title': "\"\"",
            'description': '#caughtonNestCam',
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)
        video_id = self._search_regex(
            r'https:\/\/video.nest.com\/clip\/(.+?)(\.|")', webpage, 'video_id', fatal=False)
        title = self._html_search_meta(['og:title', 'title'], webpage, 'title')
        if title == "":
            title = "\"\""
        description = self._html_search_meta(['og:description', 'description'], webpage, 'description')
        ext = self._html_search_meta('og:video:type', webpage, 'ext')
        if "/" in ext:
            ext = ext[ext.index("/") + 1:]
        return {
            'url': self._html_search_meta(['og:video:url', 'url'], webpage, 'url'),
            'id': video_id,
            'title': title,
            'description': description,
            'ext': ext,
            'thumbnail': self._html_search_meta(['og:image', 'image'], webpage, 'thumbnail'),
        }