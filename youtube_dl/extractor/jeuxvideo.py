import json
import re

from .common import InfoExtractor

class JeuxVideoIE(InfoExtractor):
    _VALID_URL = r'http://.*?\.jeuxvideo\.com/.*/(.*?)-\d+\.htm'

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        title = re.match(self._VALID_URL, url).group(1)
        webpage = self._download_webpage(url, title)
        m_download = re.search(r'<param name="flashvars" value="config=(.*?)" />', webpage)

        xml_link = m_download.group(1)
        
        id = re.search(r'http://www.jeuxvideo.com/config/\w+/0011/(.*?)/\d+_player\.xml', xml_link).group(1)

        xml_config = self._download_webpage(xml_link, title,
                                                  'Downloading XML config')
        info = re.search(r'<format\.json>(.*?)</format\.json>',
                         xml_config, re.MULTILINE|re.DOTALL).group(1)
        info = json.loads(info)['versions'][0]
        
        video_url = 'http://video720.jeuxvideo.com/' + info['file']

        track_info = {'id':id,
                      'title' : title,
                      'ext' :   'mp4',
                      'url' :   video_url
                      }

        return [track_info]
