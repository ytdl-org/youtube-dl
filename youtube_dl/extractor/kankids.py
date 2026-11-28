# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
import re

CONTENT_DIR = r'/content/kids/'
DOMAIN = r'kankids.org.il'


class KanKidsIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?' +\
        DOMAIN.replace('.', '\\.') + CONTENT_DIR +\
        r'(?P<category>[a-z]+)-main/(?P<id>[\w\-0-9]+)/(?P<season>\w+)?/?$'
    _TESTS = [
        {
            'url': 'https://www.kankids.org.il/content/kids/ktantanim-main/p-11732/',
            'info_dict': {
                '_type': 'playlist',
                'id': 'p-11732',
                'title': 'בית ספר לקוסמים',
            },
            'playlist_count': 60,
        },
        {
            'url': 'https://www.kankids.org.il/content/kids/hinuchit-main/cramel_main/s1/',
            'info_dict': {
                '_type': 'playlist',
                'id': 'cramel_main',
                'title': 'כראמל - עונה 1',
            },
            'playlist_count': 21,
        },
    ]

    def _real_extract(self, url):
        m = super()._match_valid_url(url)
        series_id = m.group('id')
        category = m.group('category')
        playlist_season = m.group('season')

        webpage = self._download_webpage(url, series_id)

        title_pattern = r'<title>(?P<title>.+) \|'
        series_title = re.search(title_pattern, webpage)
        if not series_title:
            series_title = re.search(title_pattern[:-1] + r'-', webpage)
        if series_title:
            series_title = series_title.group('title')

        season = playlist_season if playlist_season else r'(?P<season>\w+)'
        content_dir = CONTENT_DIR + category + r'-main/'
        playlist = set(re.findall(
            r'href="' + content_dir         # Content dir
            + series_id + r'/'              # Series
            + season + r'/'                 # Season
            + r'(?P<id>[0-9]+)/"'           # Episode
            + r'.+title="(?P<title>.+)"',   # Title
            webpage))

        entries = []
        content_dir = r'https://www.' + DOMAIN + content_dir
        for season, video_id, title in playlist if not playlist_season else map(lambda episode: (playlist_season,) + episode, playlist):
            entries.append(self.url_result(
                content_dir + season + r'/' + video_id + r'/',
                ie='Generic',
                video_id=video_id,
                video_title=title,
            ))

        return {
            '_type': 'playlist',
            'id': series_id,
            'title': series_title,
            'entries': entries,
        }
