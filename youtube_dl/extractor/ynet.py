# coding: utf-8
from __future__ import unicode_literals

import re
import base64
import json

from .common import InfoExtractor
from youtube_dl.utils import compat_urllib_parse_urlparse, compat_urllib_parse

class YnetIE(InfoExtractor):
    _VALID_URL = r'http://.*ynet\.co\.il/.*/0,7340,(?P<id>L(-[0-9]+)+),00\.html'
    _TEST = {
        'url': 'http://hot.ynet.co.il/home/0,7340,L-11659-99244,00.html',
        'info_dict': {
            'id': 'L-11659-99244',
            'ext': 'flv',
            'title': 'md5:3dba12d2837ee2ad9652cc64af652b16',
            'thumbnail': 'http://hot.ynet.co.il/PicServer4/2014/09/23/5606015/AMERICAN_COMMUNE1_T.jpg',
        }
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        
        id = mobj.group('id')
        
        webpage = self._download_webpage(url, id)

        content = compat_urllib_parse.unquote_plus(self._og_search_video_url(webpage).decode('utf-8'))

        player_url = re.match('(http.*\.swf)\?' ,content).group(1)
        
        config = json.loads(re.match('.*config\=(.*)' ,content).group(1))
                
        f4m_url = config['clip']['url']    

        title = re.sub(': Video$', '', self._og_search_title(webpage))

        return {
            'id': id,
            'title': title,
            'formats': self._extract_f4m_formats(f4m_url, id),
            'thumbnail': self._og_search_thumbnail(webpage),
            'player_url': player_url,
        }

