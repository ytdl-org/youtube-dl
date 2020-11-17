# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor


class TOKFMIE(InfoExtractor):
    _VALID_URL = r'https?://audycje\.tokfm\.pl/podcast/[^/]+/(?P<id>[0-9]+)'
    _TEST = {
        'url': 'http://audycje.tokfm.pl/podcast/Dr-Irena-Ozog-dr-Boguslaw-Grabowski-i-prof-Michal-Brzezinski/52972',
        'md5': '2047ca2976c616d18f8618946b62c3ed',
        'info_dict': {
            'id': '52972',
            'ext': 'mp3',
            'title': 'Dr Irena Ożóg, dr Bogusław Grabowski i prof. Michał Brzeziński',
            'description': 'Czy wróciły inwestycje? Jakie perspektywy dla wzrostu PKB?'
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)
        title = self._html_search_regex(r'<h1>(.+?)</h1>', webpage, 'title')
        description = self._html_search_regex(r'<div class=content>(.+?)</div>', webpage, None)
        js = self._download_json('http://audycje.tokfm.pl/gets', video_id, data='{"pid": %s, "st": "tokfm"}' % video_id)
        return {
            'id': video_id,
            'title': title,
            'description': description,
            'url': js['url'],
            'ext': 'mp3'
        }
