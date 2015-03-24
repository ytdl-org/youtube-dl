from __future__ import unicode_literals

from .novamov import NovaMovIE


class DivxStageIE(NovaMovIE):
    IE_NAME = 'divxstage'
    IE_DESC = 'DivxStage'

    _VALID_URL = NovaMovIE._VALID_URL_TEMPLATE % {'host': 'divxstage\.(?:eu|net|ch|co|at|ag|to)'}

    _HOST = 'www.divxstage.eu'

    _FILE_DELETED_REGEX = r'>This file no longer exists on our servers.<'
    _TITLE_REGEX = r'<div class="video_det">\s*<strong>([^<]+)</strong>'
    _DESCRIPTION_REGEX = r'<div class="video_det">\s*<strong>[^<]+</strong>\s*<p>([^<]+)</p>'

    _TEST = {
        'url': 'http://www.divxstage.eu/video/57f238e2e5e01',
        'md5': '63969f6eb26533a1968c4d325be63e72',
        'info_dict': {
            'id': '57f238e2e5e01',
            'ext': 'flv',
            'title': 'youtubedl test video',
            'description': 'This is a test video for youtubedl.',
        }
    }
