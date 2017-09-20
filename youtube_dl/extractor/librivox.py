# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    orderedSet
)


class LibriVoxIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?librivox\.org/(?P<id>(?P<title>(?:[^\-]*\-)+[^\-]*)\-by\-(?P<author>(-.*\-)*[^/]*))/?'
    _TESTS = [{
        'url': 'https://librivox.org/the-art-of-war-by-sun-tzu/',
        'info_dict': {
            'id': 'the-art-of-war-by-sun-tzu',
            'title': 'The Art Of War by Sun Tzu'
        },
        'playlist_mincount': 7
    }, {
        'url': 'https://librivox.org/alexander-the-great-by-jacob-abbott/',
        'info_dict': {
            'id': 'alexander-the-great-by-jacob-abbott',
            'title': 'Alexander The Great by Jacob Abbott'
        },
        'playlist_mincount': 12
    }]

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)

        video_id = mobj.group('id')
        book_title = mobj.group('title').replace('-', ' ').strip().title()
        author = mobj.group('author').replace('-', ' ').strip().title()

        info = {
            'id': video_id,
            '_type': 'playlist',
            'title': book_title + ' by ' + author
        }

        webpage = self._download_webpage(url, video_id)

        links = orderedSet(re.findall(r'<a href="(https?://(?:www\.)?archive\.org/download/[^/]*/([^\.]*(?<!(?:64kb)))\.mp3)".*>(.*)</a>', webpage))
        info['entries'] = [self.url_result(link[0], video_id=link[1], video_title=link[2]) for link in links]

        return info
