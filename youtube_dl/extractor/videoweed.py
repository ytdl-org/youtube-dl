from __future__ import unicode_literals

from .novamov import NovaMovIE


class VideoWeedIE(NovaMovIE):
    IE_NAME = 'videoweed'
    IE_DESC = 'VideoWeed'

    _VALID_URL = NovaMovIE._VALID_URL_TEMPLATE % {'host': 'videoweed\.(?:es|com)'}

    _HOST = 'www.videoweed.es'

    _FILE_DELETED_REGEX = r'>This file no longer exists on our servers.<'
    _TITLE_REGEX = r'<h1 class="text_shadow">([^<]+)</h1>'

    _TEST = {
        'url': 'http://www.videoweed.es/file/b42178afbea14',
        'md5': 'abd31a2132947262c50429e1d16c1bfd',
        'info_dict': {
            'id': 'b42178afbea14',
            'ext': 'flv',
            'title': 'optical illusion  dissapeared image magic illusion',
            'description': ''
        },
    }
