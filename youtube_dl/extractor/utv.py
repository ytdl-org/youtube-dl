import re

from .common import InfoExtractor

class UTVIE(InfoExtractor):
    _VALID_URL = r'http://utv.unistra.fr/index.php\?id_video\=(\d+)'

    def _real_extract(self, url):
        id = re.match(self._VALID_URL, url).group(1)
        webpage = self._download_webpage(url, id)
        url = re.search(r'file: "(.*?)",', webpage).group(1)
        title = re.search(r'/utv/\d+/.*/(.*?).mp4', url).group(1)
        
        video_url = 'http://vod-flash.u-strasbg.fr:8080/' + url

        track_info = {'id':id,
                      'title' : title,
                      'ext' :   'mp4',
                      'url' :   video_url
                      }

        return [track_info]
