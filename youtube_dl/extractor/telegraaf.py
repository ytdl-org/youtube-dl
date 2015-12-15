# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import remove_end


class TelegraafIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?telegraaf\.nl/tv/(?:[^/]+/)+(?P<id>\d+)/[^/]+\.html'
    _TEST = {
        'url': 'http://www.telegraaf.nl/tv/nieuws/binnenland/24353229/__Tikibad_ontruimd_wegens_brand__.html',
        'md5': '83245a9779bcc4a24454bfd53c65b6dc',
        'info_dict': {
            'id': '24353229',
            'ext': 'mp4',
            'title': 'Tikibad ontruimd wegens brand',
            'description': 'md5:05ca046ff47b931f9b04855015e163a4',
            'thumbnail': 're:^https?://.*\.jpg$',
            'duration': 33,
        },
    }

    def _real_extract(self, url):
        playlist_id = self._match_id(url)

        webpage = self._download_webpage(url, playlist_id)

        playlist_url = self._search_regex(
            r"iframe\.loadPlayer\('([^']+)'", webpage, 'player')

        entries = self._extract_xspf_playlist(playlist_url, playlist_id)
        title = remove_end(self._og_search_title(webpage), ' - VIDEO')
        description = self._og_search_description(webpage)

        return self.playlist_result(entries, playlist_id, title, description)
