from __future__ import unicode_literals

import re

from .common import InfoExtractor


class BildIE(InfoExtractor):
    IE_NAME = 'bild'
    _TEST = {
        'url': 'http://www.bild.de/video/clip/apple-ipad-air/das-koennen-die-neuen-ipads-38184146.bild.html',
        'info_dict': {
            'id': '38184146',
            'title': 'BILD hat sie getestet',
            'thumbnail': 'http://bilder.bild.de/fotos/stand-das-koennen-die-neuen-ipads-38184138/Bild/1.bild.jpg',
            'duration': 196,
        }
    }
    
    #http://www.bild.de/video/clip/apple-ipad-air/das-koennen-die-neuen-ipads-38184146.bild.html
    _VALID_URL = r'http?://(?:www\.)?bild\.de/(?:[^/]+/)+(?P<display_id>[^/]+)-(?P<id>\d+)(?:,auto=true)?\.bild\.html'
    
    def _real_extract(self, url):
        m = re.match(self._VALID_URL, url)
        video_id = m.group('id')
        
        #webpage = self._download_webpage(url, video_id)
        
        xml_url = url.split(".bild.html")[0]+",view=xml.bild.xml"
        
        doc = self._download_xml(xml_url, video_id)
        
        video_url = doc.attrib['src']
        title = doc.attrib['ueberschrift']
        description = doc.attrib['text']
        thumbnail = doc.attrib['img']
        duration = int(doc.attrib['duration'])/1000

        return {
            'id': video_id,
            'title': title,
            'description': description,
            'url': video_url,
            'thumbnail': thumbnail,
            'duration': duration,
        }
