# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import (
    int_or_none,
)


class FiveTVIE(InfoExtractor):
    _VALID_URL = r'http://(?:www\.)?5-tv\.ru/[^/]*/(?P<id>\d+)'
    _TESTS = [
        {
            'url': 'http://5-tv.ru/news/96814/',
            'md5': 'bbff554ad415ecf5416a2f48c22d9283',
            'info_dict': {
                'id': '96814',
                'ext': 'mp4',
                'title': 'Россияне выбрали имя для общенациональной платежной системы',
                'description': 'md5:a8aa13e2b7ad36789e9f77a74b6de660',
                'thumbnail': 're:^https?://.*\.jpg$',
                'width': 480,
                'height': 360,
                'duration': 180,
            },
        },
        {
            'url': 'http://5-tv.ru/video/1021729/',
            'md5': '299c8b72960efc9990acd2c784dc2296',
            'info_dict': {
                'id': '1021729',
                'ext': 'mp4',
                'title': '3D принтер',
                'description': 'md5:d76c736d29ef7ec5c0cf7d7c65ffcb41',
                'thumbnail': 're:^https?://.*\.jpg$',
                'width': 480,
                'height': 360,
                'duration': 180,
            },
        },
    ]

    def _real_extract(self, url):
        video_id = self._match_id(url)

        webpage = self._download_webpage(url, video_id)

        video_link = self._search_regex(
            r'(<a.*?class="videoplayer">)', webpage, 'video link')

        url = self._search_regex(r'href="([^"]+)"', video_link, 'video url')
        width = int_or_none(self._search_regex(
            r'width:(\d+)px', video_link, 'width', default=None, fatal=False))
        height = int_or_none(self._search_regex(
            r'height:(\d+)px', video_link, 'height', default=None, fatal=False))
        duration = int_or_none(self._og_search_property(
            'video:duration', webpage, 'duration'))
        return {
            'id': video_id,
            'url': url,
            'width': width,
            'height': height,
            'title': self._og_search_title(webpage),
            'description': self._og_search_description(webpage),
            'thumbnail': self._og_search_thumbnail(webpage),
            'duration': duration,
        }
