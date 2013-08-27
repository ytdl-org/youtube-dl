# coding: utf-8

import re
import json

from .common import InfoExtractor
from ..utils import determine_ext

class C56IE(InfoExtractor):
    _VALID_URL = r'https?://((www|player)\.)?56\.com/(.+?/)?(v_|(play_album.+-))(?P<textid>.+?)\.(html|swf)'
    IE_NAME = u'56.com'

    _TEST ={
        u'url': u'http://www.56.com/u39/v_OTM0NDA3MTY.html',
        u'file': u'93440716.flv',
        u'md5': u'e59995ac63d0457783ea05f93f12a866',
        u'info_dict': {
            u'title': u'网事知多少 第32期：车怒',
        },
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url, flags=re.VERBOSE)
        text_id = mobj.group('textid')
        info_page = self._download_webpage('http://vxml.56.com/json/%s/' % text_id,
                                           text_id, u'Downloading video info')
        info = json.loads(info_page)['info']
        best_format = sorted(info['rfiles'], key=lambda f: int(f['filesize']))[-1]
        video_url = best_format['url']

        return {'id': info['vid'],
                'title': info['Subject'],
                'url': video_url,
                'ext': determine_ext(video_url),
                'thumbnail': info.get('bimg') or info.get('img'),
                }
