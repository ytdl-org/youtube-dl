from __future__ import unicode_literals

from .novamov import NovaMovIE


class NowVideoIE(NovaMovIE):
    IE_NAME = 'nowvideo'
    IE_DESC = 'NowVideo'

    _VALID_URL = NovaMovIE._VALID_URL_TEMPLATE % {'host': 'nowvideo\.(?:to|ch|ec|sx|eu|at|ag|co|li)'}

    _HOST = 'www.nowvideo.to'

    _TEST = {
        'url': 'http://www.nowvideo.ch/video/0mw0yow7b6dxa',
        'md5': 'f8fbbc8add72bd95b7850c6a02fc8817',
        'info_dict': {
            'id': '0mw0yow7b6dxa',
            'ext': 'flv',
            'title': 'youtubedl test video _BaW_jenozKc.mp4',
            'description': 'Description',
        }
    }
