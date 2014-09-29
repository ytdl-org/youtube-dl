# coding: utf-8
from __future__ import unicode_literals

import re
import json
import sys

from .common import InfoExtractor
from ..utils import compat_urllib_parse, ExtractorError


class KaraoketvIE(InfoExtractor):
    _VALID_URL = r'http://karaoketv\.co\.il/\?container=songs&id=(?P<id>[0-9]+)'
    _TEST = {
        'url': 'http://karaoketv.co.il/?container=songs&id=171568',
        'info_dict': {
            'id': '171568',
            'ext': 'mp4',
            'title': 'אל העולם שלך - רותם כהן - שרים קריוקי',
        }
    }

    def _real_extract(self, url):

        # BUG: SSL23_GET_SERVER_HELLO:unknown protocol 
        if sys.hexversion < 0x03000000:
            raise ExtractorError("Only python 3 supported.\n")

        mobj = re.match(self._VALID_URL, url)
        
        video_id = mobj.group('id')

        webpage = self._download_webpage(url, video_id)

        settings_json = compat_urllib_parse.unquote_plus(self._search_regex(r'config=(.*)', self._og_search_video_url(webpage ,video_id), ''))
        
        urls_info_webpage = self._download_webpage(settings_json, 'Downloading settings json')

        urls_info_json = json.loads(urls_info_webpage.replace('\'', '"'))

        url = urls_info_json['playlist'][0]['url']

        return {
            'id': video_id,
            'title': self._og_search_title(webpage),
            'url': url,
        }