# coding: utf-8
import re

from .common import InfoExtractor


class Canalc2IE(InfoExtractor):
    IE_NAME = 'canalc2.tv'
    _VALID_URL = r'http://.*?\.canalc2\.tv/video\.asp\?.*?idVideo=(?P<id>\d+)'

    _TEST = {
        u'url': u'http://www.canalc2.tv/video.asp?idVideo=12163&voir=oui',
        u'file': u'12163.mp4',
        u'md5': u'060158428b650f896c542dfbb3d6487f',
        u'info_dict': {
            u'title': u'Terrasses du Numérique'
        }
    }

    def _real_extract(self, url):
        video_id = re.match(self._VALID_URL, url).group('id')
        # We need to set the voir field for getting the file name
        url = 'http://www.canalc2.tv/video.asp?idVideo=%s&voir=oui' % video_id
        webpage = self._download_webpage(url, video_id)
        file_name = self._search_regex(
            r"so\.addVariable\('file','(.*?)'\);",
            webpage, 'file name')
        video_url = 'http://vod-flash.u-strasbg.fr:8080/' + file_name

        title = self._html_search_regex(
            r'class="evenement8">(.*?)</a>', webpage, u'title')
        
        return {'id': video_id,
                'ext': 'mp4',
                'url': video_url,
                'title': title,
                }
