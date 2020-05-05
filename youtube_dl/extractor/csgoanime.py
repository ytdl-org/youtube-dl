# coding: utf-8
from __future__ import unicode_literals


from .common import InfoExtractor


class CSGOAnimeIE(InfoExtractor):
    _VALID_URL = r'(?:https?://)?(?:www\.)?csgoani\.me/(?P<id>[0-9A-Za-z]+)(?:/[0-9A+Za+z])*'
    _TEST = {
        'url': 'https://csgoani.me/valorant',
        'md5': 'feca224e0fd505403206f28da862601d',
        'info_dict': {
            'id': 'valorant',
            'ext': 'webm',
            'title': 'CSGOAnime',
            'uploader': 'thrice',
            'url': 'https://csgoani.me/uploads/alorant.webm'
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        video_url = self._og_search_url(webpage)

        return {
            'id': video_id,
            'ext': 'webm',
            'title': 'CSGOAnime',
            'uploader': 'thrice',
            'url': video_url
        }
