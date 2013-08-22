# coding: utf-8

import json
import re
import xml.etree.ElementTree

from .common import InfoExtractor

class JeuxVideoIE(InfoExtractor):
    _VALID_URL = r'http://.*?\.jeuxvideo\.com/.*/(.*?)-\d+\.htm'

    _TEST = {
        u'url': u'http://www.jeuxvideo.com/reportages-videos-jeux/0004/00046170/tearaway-playstation-vita-gc-2013-tearaway-nous-presente-ses-papiers-d-identite-00115182.htm',
        u'file': u'5182.mp4',
        u'md5': u'e0fdb0cd3ce98713ef9c1e1e025779d0',
        u'info_dict': {
            u'title': u'GC 2013 : Tearaway nous présente ses papiers d\'identité',
            u'description': u'Lorsque les développeurs de LittleBigPlanet proposent un nouveau titre, on ne peut que s\'attendre à un résultat original et fort attrayant.\n',
        },
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        title = re.match(self._VALID_URL, url).group(1)
        webpage = self._download_webpage(url, title)
        m_download = re.search(r'<param name="flashvars" value="config=(.*?)" />', webpage)

        xml_link = m_download.group(1)
        
        id = re.search(r'http://www.jeuxvideo.com/config/\w+/0011/(.*?)/\d+_player\.xml', xml_link).group(1)

        xml_config = self._download_webpage(xml_link, title,
                                                  'Downloading XML config')
        config = xml.etree.ElementTree.fromstring(xml_config.encode('utf-8'))
        info = re.search(r'<format\.json>(.*?)</format\.json>',
                         xml_config, re.MULTILINE|re.DOTALL).group(1)
        info = json.loads(info)['versions'][0]
        
        video_url = 'http://video720.jeuxvideo.com/' + info['file']

        return {'id': id,
                'title' : config.find('titre_video').text,
                'ext' : 'mp4',
                'url' : video_url,
                'description': self._og_search_description(webpage),
                'thumbnail': config.find('image').text,
                }
