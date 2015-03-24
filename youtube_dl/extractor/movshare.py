from __future__ import unicode_literals

from .novamov import NovaMovIE


class MovShareIE(NovaMovIE):
    IE_NAME = 'movshare'
    IE_DESC = 'MovShare'

    _VALID_URL = NovaMovIE._VALID_URL_TEMPLATE % {'host': 'movshare\.(?:net|sx|ag)'}

    _HOST = 'www.movshare.net'

    _FILE_DELETED_REGEX = r'>This file no longer exists on our servers.<'
    _TITLE_REGEX = r'<strong>Title:</strong> ([^<]+)</p>'
    _DESCRIPTION_REGEX = r'<strong>Description:</strong> ([^<]+)</p>'

    _TEST = {
        'url': 'http://www.movshare.net/video/559e28be54d96',
        'md5': 'abd31a2132947262c50429e1d16c1bfd',
        'info_dict': {
            'id': '559e28be54d96',
            'ext': 'flv',
            'title': 'dissapeared image',
            'description': 'optical illusion  dissapeared image  magic illusion',
        }
    }
