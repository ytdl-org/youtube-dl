# encoding: utf-8
from .canalplus import CanalplusIE


class D8IE(CanalplusIE):
    _VALID_URL = r'https?://www\.d8\.tv/.*?/(?P<path>.*)'
    _VIDEO_INFO_TEMPLATE = 'http://service.canal-plus.com/video/rest/getVideosLiees/d8/%s'
    IE_NAME = u'd8.tv'

    _TEST = {
        u'url': u'http://www.d8.tv/d8-docs-mags/pid6589-d8-campagne-intime.html',
        u'file': u'966289.flv',
        u'info_dict': {
            u'title': u'Campagne intime - Documentaire exceptionnel',
            u'description': u'md5:d2643b799fb190846ae09c61e59a859f',
            u'upload_date': u'20131108',
        },
        u'params': {
            # rtmp
            u'skip_download': True,
        },
    }
