# coding: utf-8
from __future__ import unicode_literals

import re
import json

from .common import InfoExtractor


class C56IE(InfoExtractor):
    _VALID_URL = r'https?://((www|player)\.)?56\.com/(.+?/)?(v_|(play_album.+-))(?P<textid>.+?)\.(html|swf)'
    IE_NAME = '56.com'
    _TEST = {
        'url': 'http://www.56.com/u39/v_OTM0NDA3MTY.html',
        'file': '93440716.flv',
        'md5': 'e59995ac63d0457783ea05f93f12a866',
        'info_dict': {
            'title': '网事知多少 第32期：车怒',
        },
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url, flags=re.VERBOSE)
        text_id = mobj.group('textid')
        info_page = self._download_webpage('http://vxml.56.com/json/%s/' % text_id,
                                           text_id, 'Downloading video info')
        info = json.loads(info_page)['info']
        formats = [{
            'format_id': f['type'],
            'filesize': int(f['filesize']),
            'url': f['url']
        } for f in info['rfiles']]
        self._sort_formats(formats)

        return {
            'id': info['vid'],
            'title': info['Subject'],
            'formats': formats,
            'thumbnail': info.get('bimg') or info.get('img'),
        }
