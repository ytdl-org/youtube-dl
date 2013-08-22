# coding: utf-8
"""Extractor for canalc2.tv"""
import re
import lxml.html

from .common import InfoExtractor

class Canalc2IE(InfoExtractor):
    """Extractor for canalc2.tv"""
    _VALID_URL = r'http://.*?\.canalc2\.tv/video\.asp\?idVideo=(\d+)&voir=oui'

    _TEST = {
        u'url': u'http://www.canalc2.tv/video.asp?idVideo=12163&voir=oui',
        u'file': u'12163.mp4',
        u'md5': u'c00fa80517373764ff5c0b5eb5a58780',
        u'info_dict': {
            u'title': u'Terrasses du Numérique'
        }
    }

    def _real_extract(self, url):
        video_id = re.match(self._VALID_URL, url).group(1)
        webpage = self._download_webpage(url, video_id)
        file_name = re.search(r"so\.addVariable\('file','(.*?)'\);",
            webpage).group(1)
        
        video_url = 'http://vod-flash.u-strasbg.fr:8080/' + file_name
        
        html   = lxml.html.fromstring(webpage)
        
        title = html.cssselect('.evenement8')[0].text_content()
        
        return {'id': video_id,
                'ext' : 'mp4',
                'url' : video_url,
                'title' : title
                }
