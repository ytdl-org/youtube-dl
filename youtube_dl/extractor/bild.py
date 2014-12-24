# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import int_or_none


class BildIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?bild\.de/(?:[^/]+/)+(?P<display_id>[^/]+)-(?P<id>\d+)(?:,auto=true)?\.bild\.html'
    IE_DESC = 'Bild.de'
    _TEST = {
        'url': 'http://www.bild.de/video/clip/apple-ipad-air/das-koennen-die-neuen-ipads-38184146.bild.html',
        'md5': 'dd495cbd99f2413502a1713a1156ac8a',
        'info_dict': {
            'id': '38184146',
            'ext': 'mp4',
            'title': 'BILD hat sie getestet',
            'thumbnail': 'http://bilder.bild.de/fotos/stand-das-koennen-die-neuen-ipads-38184138/Bild/1.bild.jpg',
            'duration': 196,
            'description': 'Mit dem iPad Air 2 und dem iPad Mini 3 hat Apple zwei neue Tablet-Modelle präsentiert. BILD-Reporter Sven Stein durfte die Geräte bereits testen. ',
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)

        xml_url = url.split(".bild.html")[0] + ",view=xml.bild.xml"
        doc = self._download_xml(xml_url, video_id)

        duration = int_or_none(doc.attrib.get('duration'), scale=1000)

        return {
            'id': video_id,
            'title': doc.attrib['ueberschrift'],
            'description': doc.attrib.get('text'),
            'url': doc.attrib['src'],
            'thumbnail': doc.attrib.get('img'),
            'duration': duration,
        }
