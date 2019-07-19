# coding: utf-8
from __future__ import unicode_literals

from .zdf import ZDFIE


class DreiSatIE(ZDFIE):
    _VALID_URL = r'https?://www\.3sat\.de/(?:[^/]+/)*(?P<id>[^/?]+)\.html'
    _TESTS = [{
         'url': 'https://www.3sat.de/dokumentation/natur/dolomiten-sagenhaftes-juwel-der-alpen-100.html',
         'info_dict': {
             'id': 'dolomiten-sagenhaftes-juwel-der-alpen-100',
             'ext': 'mp4',
             'title': 'Dolomiten - Sagenhaftes Juwel der Alpen',
             'description': 'md5:a4fa13cae91b8044353c1d56f3a8fc77',
             'duration': 2618,
             'timestamp': 1561397400,
             'upload_date': '20190624',
         },
    }, {
        'url': 'https://www.3sat.de/kultur/festspielsommer/anna-netrebko-arena-di-verona-il-trovatore-musik-100.html',
        'only_matching': True,
    }, {
        'url': 'https://www.3sat.de/kultur/theater-und-tanz/nibelungen-ueberwaeltigung-100.html',
        'only_matching': True,
    }]

    pass

