# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor


class BajeczkiIE(InfoExtractor):
    _VALID_URL = r'http?://(?:www\.)?bajeczki\.org/(?P<id>.*)'
    _TEST = {
        'url': 'http://bajeczki.org/psi-patrol/pieski-ratuja-przyjaciol-ksiezniczki/',
        'md5': '01f72e7e641448785db6a9bd77a94b31',
        'info_dict': {
            'id': 'psi-patrol/pieski-ratuja-przyjaciol-ksiezniczki/',
            'ext': 'mp4',
            'title': 'Psi Patrol - Psia misja: Pieski ratują przyjaciół księżniczki',
        },
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)

        webpage = self._download_webpage(url, video_id)

        url = self._search_regex(r'(http.*\.mp4)', webpage, 'url').replace('\\', '')

        title = self._html_search_regex(r'<title>(.+?)</title>', webpage, 'title').split(' |', 1)[0]

        return {
            'id': video_id,
            'url': url,
            'title': title,
        }
