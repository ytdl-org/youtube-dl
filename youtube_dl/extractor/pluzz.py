import re

from .common import InfoExtractor


class PluzzIE(InfoExtractor):
    _IE_NAME = 'canalc2.tv'
    _VALID_URL = r'http://pluzz\.francetv\.fr/videos/(.*?)\.html'

    _TEST = {
        u'url': u'http://pluzz.francetv.fr/videos/doctor_who.html',
        u'file': u'88444506.mp4'
    }

    def _real_extract(self, url):
        title = re.match(self._VALID_URL, url).group(1)
        webpage = self._download_webpage(url, title)
        thumbnail = self._search_regex(
            r'itemprop="thumbnailUrl" content="(.*?)"', webpage, 'thumbnail')
            
        video_id = self._search_regex(
            r'data-diffusion="(\d+)"', webpage, 'ID')
        xml_desc = self._download_webpage(
            'http://www.pluzz.fr/appftv/webservices/video/'
            'getInfosOeuvre.php?id-diffusion='
            + video_id, title, 'Downloading XML config')
        
        manifest_url = self._search_regex(r'<url><\!\[CDATA\[(.*?)]]></url>',
            xml_desc, re.MULTILINE|re.DOTALL)
        video_url = manifest_url.replace('manifest.f4m', 'index_2_av.m3u8')
        video_url = video_url.replace('/z/', '/i/')
        
        return {'id': video_id,
                'ext': 'mp4',
                'url': video_url,
                'title': title,
                'thumbnail': thumbnail
                }
