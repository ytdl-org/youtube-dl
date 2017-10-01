# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import orderedSet


class LibriVoxIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?librivox\.org/(?P<id>(?P<title>(?:[^\-]*\-)+[^\-]*)\-by\-(?P<author>(-.*\-)*[^/]*))/?'
    _TESTS = [{
        'url': 'https://librivox.org/the-art-of-war-by-sun-tzu/',
        'info_dict': {
            'id': 'the-art-of-war-by-sun-tzu',
            'title': 'The Art Of War by Sun Tzu',
            'description': '"The Art of War is a Chinese military treatise written during the 6th century BC by Sun Tzu. Composed of 13 chapters, each of which is devoted to one aspect of warfare, it has long been praised as the definitive work on military strategies and tactics of its time. The Art of War is one of the oldest and most famous studies of strategy and has had a huge influence on both military planning and beyond. The Art of War has also been applied, with much success, to business and managerial strategies." (summary from Wikipedia)'
        },
        'playlist_mincount': 7
    }, {
        'url': 'https://librivox.org/alexander-the-great-by-jacob-abbott/',
        'info_dict': {
            'id': 'alexander-the-great-by-jacob-abbott',
            'title': 'Alexander The Great by Jacob Abbott',
            'description': 'Alexander the Great was one of the most successful military commanders in history, and was undefeated in battle. By the time of his death, he had conquered most of the world known to the ancient Greeks.\nAlexander the Great is one of many biographies aimed at young people written by Jacob Abbott and his brother. The biographies are written in such a way that makes them appealing and easily accessible to everyone. - Written by Wikipedia and Lizzie Driver'
        },
        'playlist_mincount': 12
    }]

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)

        video_id = mobj.group('id')

        webpage = self._download_webpage(url, video_id)

        book_title = self._html_search_regex(
            r'<h1>(?P<title>.+)</h1>', webpage, 'title', group='title', fatal=False).lower().title() or mobj.group('title').replace('-', ' ').strip().title()
        author = mobj.group('author').replace('-', ' ').strip().title()
        description = self._html_search_regex(
            r'<div class=(["\'])description\1(^>)*>(<p(^>)*>)?(?P<desc>.+)(</p>)?</div>',
            webpage, 'description', group='desc', fatal=False) or self._og_search_description(webpage)

        info = {
            'id': video_id,
            '_type': 'playlist',
            'title': book_title + ' by ' + author,
            'description': description
        }

        links = orderedSet(re.findall(r'<a href=(["\'])(https?://(?:www\.)?archive\.org/download/[^/]*/([^\.]*(?<!(?:64kb)))\.mp3)\1.*>(.*)</a>', webpage))
        info['entries'] = [self.url_result(link[1], video_id=link[2], video_title=link[3]) for link in links]

        return info
