# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import int_or_none


class SWRMediathekIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?swrmediathek\.de/player\.htm\?show=(?P<videoid>[^?#&]+)'

    _TESTS = [{
        'url': 'http://swrmediathek.de/player.htm?show=849790d0-dab8-11e3-a953-0026b975f2e6',
        'info_dict': {
            'id': '849790d0-dab8-11e3-a953-0026b975f2e6',
            'ext': 'flv',
            'title': 'SWR odysso',
            'description': 'md5:2012e31baad36162e97ce9eb3f157b8a',
            'thumbnail': 're:^http:.*\.jpg$',
        },
        'params': {
            'skip_download': True,  # requires rtmpdump
        },
    }, {
        'url': 'http://swrmediathek.de/player.htm?show=0e1a8510-ddf2-11e3-9be3-0026b975f2e6',
        'info_dict': {
            'id': '0e1a8510-ddf2-11e3-9be3-0026b975f2e6',
            'ext': 'flv',
            'title': 'Nachtcafé - Alltagsdroge Alkohol - zwischen Sektempfang und Komasaufen',
            'description': 'md5:e0a3adc17e47db2c23aab9ebc36dbee2',
            'thumbnail': 're:http://.*\.jpg',
        },
        'params': {
            'skip_download': True,  # requires rtmpdump
        },
    }]

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('videoid')

        webpage = self._download_webpage(url, video_id)

        smilurl = 'http://swrmediathek.de/rtmpQuals/%s/clips.smil'
        smildoc = self._download_xml(smilurl % video_id, video_id, note='Downloading SMIL page')

        baseurl = smildoc.find('.//meta').attrib['base']

        formats = []
        for video in smildoc.findall('.//video'):
            vbr = video.attrib.get('system-bitrate')
            if vbr:
                vbr = int(vbr) / 1000

            formats.append({
                'format_id': video.attrib['height'] + 'p',
                'width': int_or_none(video.attrib['width']),
                'height': int_or_none(video.attrib['height']),
                'vbr': vbr,
                'url': baseurl,
                'play_path': 'mp4:' + video.attrib['src'],
                'ext': 'flv',
            })

        self._sort_formats(formats)

        return {
            'id': video_id,
            'title': self._html_search_regex(r'<meta name="title" content="(.+)" />', webpage, 'title'),
            'thumbnail': self._search_regex(r'<link rel="image_src".+href="(.+)" />', webpage, 'thumbnail'),
            'formats': formats,
            'description': self._html_search_regex(r'<meta name="description" content="(.+)" />', webpage, 'description'),
        }
