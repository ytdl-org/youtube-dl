from __future__ import unicode_literals

from .novamov import NovaMovIE


class NowVideoIE(NovaMovIE):
    IE_NAME = 'nowvideo'
    IE_DESC = 'NowVideo'

    _VALID_URL = r'http://(?:(?:www\.)?%(host)s/video/|(?:(?:embed|www)\.)%(host)s/embed\.php\?(?:.*?&)?v=)(?P<videoid>[a-z\d]{13})' % {'host': 'nowvideo\.(?:ch|sx|eu)'}

    _HOST = 'www.nowvideo.ch'

    _FILE_DELETED_REGEX = r'>This file no longer exists on our servers.<'
    _FILEKEY_REGEX = r'var fkzd="([^"]+)";'
    _TITLE_REGEX = r'<h4>([^<]+)</h4>'
    _DESCRIPTION_REGEX = r'</h4>\s*<p>([^<]+)</p>'

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