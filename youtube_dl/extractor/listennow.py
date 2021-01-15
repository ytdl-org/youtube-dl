# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor


class ListennowIE(InfoExtractor):
    _VALID_URL = r'https?://(?:[^\.]+\.)?listennow\.link/(?P<id>\d+)'

    _TEST = {
        'url': 'https://radionorge.listennow.link/10279676',
        'info_dict': {
            'id': '2035659',
            'ext': 'mp3',
            'title': 'Best of Høsten 2020',
            'description': 'md5:701b09a2bcf9a75b6bfd8a27f359dcfa',
            'timestamp': 1603429200,
            'upload_date': '20201023',
        },
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)
        url = self._search_regex(
            r'desktopUrl\s*:\s*\'([^\']+)\'', webpage,
            'redirect', video_id)
        return self.url_result(url)
