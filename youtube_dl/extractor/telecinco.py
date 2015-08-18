# coding: utf-8
from __future__ import unicode_literals

from .mitele import MiTeleIE


class TelecincoIE(MiTeleIE):
    IE_NAME = 'telecinco.es'
    _VALID_URL = r'https?://www\.telecinco\.es/(?:[^/]+/)+(?P<id>.+?)\.html'

    _TESTS = [{
        'url': 'http://www.telecinco.es/robinfood/temporada-01/t01xp14/Bacalao-cocochas-pil-pil_0_1876350223.html',
        'info_dict': {
            'id': 'MDSVID20141015_0058',
            'ext': 'mp4',
            'title': 'Con Martín Berasategui, hacer un bacalao al ...',
            'duration': 662,
        },
        'params': {
            # m3u8 download
            'skip_download': True,
        },
    }, {
        'url': 'http://www.telecinco.es/informativos/nacional/Pablo_Iglesias-Informativos_Telecinco-entrevista-Pedro_Piqueras_2_1945155182.html',
        'only_matching': True,
    }, {
        'url': 'http://www.telecinco.es/espanasinirmaslejos/Espana-gran-destino-turistico_2_1240605043.html',
        'only_matching': True,
    }]
