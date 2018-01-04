# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor

class RtvsExtractorIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?rtvs\.sk/.*/archiv/[0-9]*/(?P<id>[0-9]+)'
    _TEST = {
        'url': 'http://www.rtvs.sk/radio/archiv/11224/414872',
        'md5': '134d5d6debdeddf8a5d761cbc9edacb8',
        'info_dict': {
            'id': '414872',
            'ext': 'mp3',
            'title': u'Ostrov pokladov 1 časť',
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)
        playlist_url = self._search_regex(r'"playlist": "(https?:.*)&', webpage, 'playlist_url')
        self.to_screen("Playlist URL: " + playlist_url)

        playlist = self._download_json(playlist_url, video_id, "Downloading playlist")
        playlist_item = playlist[0]
        url = playlist_item["sources"][0]["file"]
        full_title = playlist_item.get("title")
        (title, ext) = full_title.split(".", 2)

        return {
            'id': video_id,
            'url': url,
            'title': title,
            'ext': ext
        }
