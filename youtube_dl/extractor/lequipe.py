# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor


class LequipeIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?lequipe\.fr/video/(?P<id>.*)'
    _TEST = {
        'url': 'https://www.lequipe.fr/video/x791mem',
        'md5': '2e76bcda7c90c4c44ff4a2f2be1e711c',
        'info_dict': {
            'id': 'x791mem',
            'title': '10e étape du Giro, 2e partie - Cyclisme - Replay',
            'description': 'VIDÉO CYCLISME - Retrouvez le replay de la deuxième partie de la 10e étape du Giro 2019 entre Ravenne et Modène.',
            'ext': 'mp4',
            'timestamp': 1558539198,
            'upload_date': '20190522',
            'uploader_id': 'x1h9q8j',
            'uploader': 'la chaine L\'Équipe',
        },
    }

    def _real_extract(self, url):
        return {
            '_type': "url",
            'url': "https://www.dailymotion.com/video/" + self._match_id(url),
            'ie_key': 'Dailymotion',
        }
