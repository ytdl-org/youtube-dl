# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor

class RtvsExtractorIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?rtvs\.sk/.*/archiv/[0-9]*/(?P<id>[0-9]+)'
    _TESTS = [{
        # radio archive
        'url': 'http://www.rtvs.sk/radio/archiv/11224/414872',
        'md5': '134d5d6debdeddf8a5d761cbc9edacb8',
        'info_dict': {
            'id': '414872',
            'ext': 'mp3',
            'title': u'Ostrov pokladov 1 časť.mp3',
        }
    }, {
        # tv archive
        'url': 'http://www.rtvs.sk/televizia/archiv/8249/63118',
        'md5': '85e2c55cf988403b70cac24f5c086dc6',
        'info_dict': {
            'id': '63118',
            'ext': 'mp4',
            'title': u'Amaro Džives - Náš deň',
            'description': u'Galavečer pri príležitosti Medzinárodného dňa Rómov.'
            }
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        playlist_url = self._search_regex(r'"playlist": "(https?:.*)&', webpage, 'playlist_url')
        self.to_screen("%s: Playlist URL: %s" % (video_id, playlist_url))
        playlist = self._download_json(playlist_url, video_id, "Downloading playlist")
        jwplayer_data = playlist[0]
        return self._parse_jwplayer_data(jwplayer_data, video_id=video_id)

