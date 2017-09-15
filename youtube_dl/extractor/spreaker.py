# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    determine_ext,
    js_to_json,
)


class SpreakerIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?spreaker\.com/user/[\w]+/(?P<id>[^/?#]+)'
    _TESTS = [{
        'url': 'http://www.spreaker.com/user/dmgaming/should-madden-18-be-half-price',
        'md5': '377349c3f1f2788f8c93a9f0f71fd91e',
        'info_dict': {
            'id': 'should-madden-18-be-half-price',
            'ext': 'mp3',
            'title': 'Should Madden 18 be half price',
            'description': 'today we talk about the price for the new Madden NFL 18',
        }
    }, {
        'url': 'https://www.spreaker.com/user/gilmoreguys/lg-gab-fina2',
        'md5': '1b6d2f44d7c8e019a650af275c1e7623',
        'info_dict': {
            'id': 'lg-gab-fina2',
            'ext': 'mp3',
            'title': 'Lauren Graham',
            'description': 'Lauren Graham joins the Gilmore Guys. Thanks for listening!',
        }
    }]

    def _real_extract(self, url):
        display_id = self._match_id(url)
        webpage = self._download_webpage(url, display_id)

        title = self._og_search_title(webpage)

        description = self._og_search_description(webpage)
        url = self._search_regex(
            r'id=\"track_download\"\shref=\"(.+)\"><span',
            webpage, 'url', fatal=False)
        formats = [{
            'url': url,
            'ext': determine_ext(url, 'mp3')
        }]

        return {
            'id': display_id,
            'title': title,
            'description': description,
            'formats': formats
        }


class SpreakerPlaylistBaseIE(InfoExtractor):
    _PLAYLIST_API_URL = 'https://api.spreaker.com/show/%s/episodes?include_externals=true&page=1&max_per_page=100'

    def _download_playlist_json(self, show_id, playlist_id):
        return self._download_json(
            self._PLAYLIST_API_URL % show_id, playlist_id)['response']['pager']['results']

    def _extract_track_entries(self, playlist):
        return [
            self.url_result(
                episode.get('download_url'), SpreakerIE.ie_key()
            )
            for episode in playlist
        ]


class SpreakerPlaylistIE(SpreakerPlaylistBaseIE):
    _VALID_URL = r'https?://(?:www\.)?spreaker\.com/show/(?P<id>[^/?#]+)'
    _TESTS = [{
        'url': 'http://www.spreaker.com/show/andre-dorseys-show',
        'info_dict': {
            'id': 'andre-dorseys-show',
            'title': 'DM Gaming\'s Show',
            'description': 'Love video games and a little comedy, well you\'ve come to the right place. Welcome to the DM Gaming community. Subscribe to us on youtube at www.youtube.com/c/dmgaming06',
        },
        'playlist_count': 17,
    }, {
        'url': 'https://www.spreaker.com/show/foodstuff',
        'info_dict': {
            'id': 'foodstuff',
            'title': 'FoodStuff',
            'description': 'The stuff we eat and drink is part daily necessity and part cultural identity. Every mouthful represents millennia of human collaboration and innovation. On FoodStuff, Anney and Lauren bite into the juicy stories – and science – behind everything that nourishes us.'
        },
        'playlist_count': 30,
    }]

    def _real_extract(self, url):
        playlist_id = self._match_id(url)
        webpage = self._download_webpage(url, playlist_id)

        description = self._og_search_description(webpage)
        title = self._og_search_title(webpage)

        show_id = self._parse_json(self._search_regex(
            r'\(\'show\',\s([^)]+)\)', webpage, 'show json', fatal=False
            ), playlist_id, transform_source=js_to_json).get('show_id')

        playlist = self._download_playlist_json(show_id, playlist_id)
        entries = self._extract_track_entries(playlist)

        return self.playlist_result(entries, playlist_id, title, description)
