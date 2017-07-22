# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import unified_strdate
from datetime import datetime

class AliExpressLiveIE(InfoExtractor):
    _VALID_URL = r'https?://live\.aliexpress\.com/live/(?P<id>[0-9]{16})'
    _TEST = [{
        'url': 'https://live.aliexpress.com/live/2800002704436634',
        'info_dict': {
            'id': '2800002704436634',
            'ext': 'm3u8',
            'title': 'CASIMA7.22',
            'uploader': 'CASIMA Official Store',
            'upload_date': '20170714',
            'is_live': True,
        },
        'params': {
            'skip_download': True,
        }
    }]

    def _real_extract(self, url):
        page = self._download_webpage(url, self._match_id(url))
        upload_date = self._html_search_regex(r'"createTime":([0-9]{10})[0-9]{3},', page, 'upload_date')

        return {
            'id': str(self._match_id(url)),
            'title': self._html_search_regex(r'"title": "([^"]+)"', page, 'url'),
            'url': self._html_search_regex(r'"replyStreamUrl": "([^"]+)"', page, 'url'),
            'uploader': self._html_search_regex(r'"name":"([^"]+)"', page, 'uploader'),
            'upload_date': datetime.fromtimestamp(int(upload_date)).strftime('%Y%m%d'),
            'is_live': True,
        }
