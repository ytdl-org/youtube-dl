# coding: utf-8
from __future__ import unicode_literals

from .mitele import MiTeleIE


class TelecincoIE(MiTeleIE):
    IE_NAME = 'telecinco.es'
    _VALID_URL = r'https?://www\.telecinco\.es/[^/]+/[^/]+/[^/]+/(?P<episode>.*?)\.html'

    _TEST = {
        'url': 'http://www.telecinco.es/robinfood/temporada-01/t01xp14/Bacalao-cocochas-pil-pil_0_1876350223.html',
        'info_dict': {
            'id': 'MDSVID20141015_0058',
            'ext': 'mp4',
            'title': 'Con Martín Berasategui, hacer un bacalao al ...',
            'duration': 662,
        },
    }
