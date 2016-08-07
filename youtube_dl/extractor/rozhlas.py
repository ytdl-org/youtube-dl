# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor


class RozhlasIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?prehravac\.rozhlas\.cz/audio/(?P<id>[0-9]+)'
    _TEST = {
        'url': 'http://prehravac.rozhlas.cz/audio/3421320',
        'md5': '504c902dbc9e9a1fd50326eccf02a7e2',
        'info_dict': {
            'id': '3421320',
            'ext': 'mp3',
            'title': 'Echo Pavla Klusáka (30.06.2015 21:00)',
            'description': 'Osmdesátiny Terryho Rileyho jsou skvělou příležitostí proletět se elektronickými i akustickými díly zakladatatele minimalismu, který je aktivní už přes padesát let'
        }
    }

    def _real_extract(self, url):
        audio_id = self._match_id(url)
        webpage = self._download_webpage(url, audio_id)

        title = self._html_search_regex(r'<h3>(.+?)</h3>', webpage, 'title')
        description = self._html_search_regex(r'<p title="(.+?)">', webpage, 'description', fatal=False)

        url = 'http://media.rozhlas.cz/_audio/' + audio_id + '.mp3'

        return {
            'id': audio_id,
            'url': url,
            'title': title,
            'description': description,
        }
