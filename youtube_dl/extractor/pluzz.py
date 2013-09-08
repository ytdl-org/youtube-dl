import re

from .common import InfoExtractor


class PluzzIE(InfoExtractor):
    _IE_NAME = 'canalc2.tv'
    _VALID_URL = r'http://pluzz\.francetv\.fr/videos/(.*?)\.html'

    _TEST = {
        u'url': u'http://pluzz.francetv.fr/videos/doctor_who.html',
        u'file': u'12163.mp4',
        u'md5': u'060158428b650f896c542dfbb3d6487f'
    }

    def _real_extract(self, url):
        title = re.match(self._VALID_URL, url).group(1)
        webpage = self._download_webpage(url, title)
        thumbnail = self._search_regex(
            r'itemprop="thumbnailUrl" content="(.*?)"', webpage, 'thumbnail')
            
        video_id = self._search_regex(
            r'data-diffusion="(\d+)"', webpage, 'ID')
        xml_desc = self._download_webpage('http://www.pluzz.fr/appftv/webservices/video/getInfosOeuvre.php?id-diffusion=' + video_id, title, 'Downloading XML config')
        
        manifest_url = self._search_regex(r'<url><\!\[CDATA\[(.*?)]]></url>', xml_desc, re.MULTILINE|re.DOTALL)
        
        token = self._download_webpage('http://hdfauth.francetv.fr/esi/urltokengen2.html?url=' + manifest_url, title, 'Getting token')
        
        return {'id': video_id,
                'ext': 'f4m',
                'url': video_url,
                'title': title,
                'thumbnail': thumbnail
                }
