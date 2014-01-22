# encoding: utf-8
from __future__ import unicode_literals

from .canalplus import CanalplusIE


class D8IE(CanalplusIE):
    _VALID_URL = r'https?://www\.d8\.tv/.*?/(?P<path>.*)'
    _VIDEO_INFO_TEMPLATE = 'http://service.canal-plus.com/video/rest/getVideosLiees/d8/%s'
    IE_NAME = 'd8.tv'

    _TEST = {
        'url': 'http://www.d8.tv/d8-docs-mags/pid6589-d8-campagne-intime.html',
        'file': '966289.flv',
        'info_dict': {
            'title': 'Campagne intime - Documentaire exceptionnel',
            'description': 'md5:d2643b799fb190846ae09c61e59a859f',
            'upload_date': '20131108',
        },
        'params': {
            # rtmp
            'skip_download': True,
        },
        'skip': 'videos get deleted after a while',
    }
