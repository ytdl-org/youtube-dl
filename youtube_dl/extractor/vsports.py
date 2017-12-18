# coding: utf-8
from __future__ import unicode_literals
from urlparse import urlparse

from .common import InfoExtractor


class VSportsIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?vsports\.pt/vod/(?P<id>[0-9]+)/m/[0-9]+/vsports/[0-9a-f]+'
    _TESTS = [{
        'url': 'https://www.vsports.pt/vod/36067/m/263034/vsports/342f5e5464caa7972ce80a4ad20fc7c3',
        'md5': '880b0c0a2ce60d6deb4bf235102bf9db',
        'info_dict': {
            'id': '36067',
            'ext': 'mp4',
            'title': 'SL Benfica X FC Porto - FC Porto, Golo, Maxi Pereira, 49m, 1-1',
            'description': 'Jogada de insistência do ataque portista, com André André a rematar uma primeira vez para defesa de Éderson e na recarga Maxi Pereira fez o empate.',
            'thumbnail': r're:^https?://.*\.jpg$',
        }
    }, {
        'url': 'https://www.vsports.pt/vod/40427/m/361897/vsports/45cc7d8f9c237dbcbec1b19a57d85b6e',
        'md5': '323d7fad7d94f22d61901ae14b544c6d',
        'info_dict': {
            'id': '40427',
            'ext': 'mp4',
            'title': 'Liga NOS (15ª Jornada): Resumo FC Porto 3-1 Marítimo M.',
            'description': 'Triunfo do FC Porto, que com este resultado encerra o ano de 2017 na liderança da Liga NOS. O Marítimo ainda conseguiu empatar, mas depois viu-se reduzido a 10 unidades e acabou por não aguentar o caudal ofensivo dos portistas.',
            'thumbnail': r're:^https?://.*\.jpg$',
        },
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)
        url = self._search_regex(r'//((vod\.vsports\.pt/vdo/\w+/\w+/\w+.mp4)|(vsports\.videos\.sapo\.pt/\w+/mov/))', webpage, 'url')
        title = self._html_search_regex(r'<title>(.+?)</title>', webpage, 'title')

        return {
            'id': video_id,
            'title': title,
            'description': self._og_search_description(webpage),
            'thumbnail': self._og_search_thumbnail(webpage),
            'ext': 'mp4',
            'url': 'https://%s' % (url)
        }