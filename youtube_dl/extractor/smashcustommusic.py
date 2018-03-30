# coding: utf-8

from __future__ import unicode_literals

from .common import InfoExtractor

from ..utils import (
    urljoin,
)


_BASE_URL_ = 'https://www.smashcustommusic.com'

class SmashcustommusicIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?smashcustommusic\.com/(?P<id>[0-9]+)'
    _TESTS = [{
        'url': 'https://smashcustommusic.com/1',
        'md5': 'a5bc179893861998be3d12bfe47295a5',
        'info_dict': {
            'id': '1',
            'ext': 'mp3',
            'title': 'Chrono Cross: Ancient Dragon\'s Stronghold',
        },
    }, {
        'url': 'https://smashcustommusic.com/29660',
        'md5': '17bd3fc26e0776ca6066058e1f118520',
        'info_dict': {
            'id': '29660',
            'ext': 'mp3',
            'title': 'Gyakuten Saiban 2 (GBA): Eccentric',
        },
    }]

    def _real_extract(self, url):
        playurl = '/play/'
        song_id = self._match_id(url)
        webpage = self._download_webpage(url, song_id)

        title = self._html_search_regex(r'<h1 style="text-align:center;">(.+?)</h1>', webpage, 'title')
        url = urljoin(_BASE_URL_, playurl)
        url = urljoin(url, song_id)

        return {
            'id': song_id,
            'title': title,
            'url': url,
            'ext': 'mp3',
        }