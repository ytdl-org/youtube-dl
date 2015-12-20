# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import re

from .common import InfoExtractor

from ..utils import (
    sanitized_Request,
    xpath_with_ns,
)


class RegioTVIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?regio-tv\.de/video/(?P<id>[0-9]+).html'
    _TESTS = [
        {
            'url': 'http://www.regio-tv.de/video/395808.html',
            'info_dict': {
                'id': '395808',
                'ext': 'mp4',
                'title': u'Wir in Ludwigsburg',
                'description': u'Mit unseren zuckers\xfc\xdfen Adventskindern, au\xdferdem besuchen wir die Abendsterne!',
            }
        },
    ]

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')

        webpage = self._download_webpage(url, video_id)
        key = self._html_search_regex(r''',key: "(.*?)"''', webpage, 'key')

        title = self._html_search_regex(
            r'<meta property="og:title" content="\s*(.*?)\s*"\s*/?\s*>',
            webpage, 'title')

        soapxml = '<?xml version="1.0" encoding="utf-8"?><soap:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/"><soap:Body><getHTML5VideoData xmlns="http://v.telvi.de/"><key xsi:type="xsd:string">%s</key></getHTML5VideoData></soap:Body></soap:Envelope>' % key
        request = sanitized_Request('http://v.telvi.de/?wsdl', soapxml)
        request.add_header('Origin', 'http://www.regio-tv.de')
        request.add_header('Referer', url)
        video_data = self._download_xml(request, video_id, 'video data')

        NS_MAP = {
            'xsi': 'http://www.w3.org/2001/XMLSchema-instance',
            'soap': 'http://schemas.xmlsoap.org/soap/envelope/',
        }

        url = video_data.find(xpath_with_ns('.//video', NS_MAP)).text
        thumbnail = video_data.find(xpath_with_ns('.//image', NS_MAP)).text

        description = self._html_search_meta('description', webpage)

        return {
            'id': video_id,
            'title': title,
            'url': url,
            'thumbnail': thumbnail,
            'description': description,
        }
