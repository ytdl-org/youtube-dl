# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
import re

class KanKidsIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?kankids\.org\.il/content/kids/(?P<category>[a-z]+)-main/p-(?P<id>[0-9]+)/(?P<season>\w+)?/?$'
    _TEST = {
        'url': 'https://www.kankids.org.il/content/kids/hinuchit-main/p-12050/',
        'md5': 'TODO: md5 sum of the first 10241 bytes of the video file (use --test)',
        'info_dict': {
            'id': '42',
            'ext': 'mp4',
            'title': 'Video title goes here',
            'thumbnail': r're:^https?://.*\.jpg$',
            # TODO more properties, either as:
            # * A value
            # * MD5 checksum; start the string with md5:
            # * A regular expression; start the string with re:
            # * Any Python type (for example int or float)
        }
    }

    def _real_extract(self, url):
        m = super()._match_valid_url(url)
        series_id = m.group('id')
        category = m.group('category')
        playlist_season = m.group('season')
        
        webpage = self._download_webpage(url, series_id)

        series_title = self._html_search_regex(r'<title>(?P<title>.+) \|', webpage, 'title')

        season = playlist_season if playlist_season else '(?P<season>\w+)'
        playlist = set(re.findall(
            r'href="/content/kids/' +   # Content dir
            category + r'-main/' +      # Category
            'p-' + series_id + '/' +    # Series
            season + '/' +              # Season
            '(?P<id>[0-9]+)/"' +        # Episode
            '.+title="(?P<title>.+)"'   # Title
            , webpage))
            # , 'Episode list')
        print('playlist:', playlist)

        for season, video_id, title in playlist if not playlist_season else map(lambda episode: (playlist_season,) + episode, playlist):
            pass

        return {
            'id': series_id,
            'title': title,
            'description': self._og_search_description(webpage),
            'url': 'https://www.kankids.org.il/content/kids/hinuchit-main/p-12050/s1/89707/',
            'ie_key': 'Generic',
            '_type': 'url',
            # 'uploader': self._search_regex(r'<div[^>]+id="uploader"[^>]*>([^<]+)<', webpage, 'uploader', fatal=False),
            # TODO more properties (see youtube_dl/extractor/common.py)
            }

