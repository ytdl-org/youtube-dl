# coding: utf-8
from __future__ import unicode_literals


import re

from .common import InfoExtractor
from ..utils import try_get, float_or_none
from ..compat import compat_str


class AliExpressLiveIE(InfoExtractor):

    _VALID_URL = r'https?://live\.aliexpress\.com/live/(?P<id>[0-9]{16})'
    _TEST = {
        'url': 'https://live.aliexpress.com/live/2800002704436634',
        'md5': '7ac2bc46afdd18f0b45a0a340fc47ffe',
        'info_dict': {
            'id': '2800002704436634',
            'ext': 'm3u8',
            'title': 'CASIMA7.22',
            'uploader': 'CASIMA Official Store',
            'upload_date': '20170714',
            'timestamp': 1500027138,
        },
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        page = self._download_webpage(url, video_id)
        run_params_json = self._search_regex(r'runParams = (.+)[\s+]var myCtl', page, 'runParams', flags=re.DOTALL)
        run_params = self._parse_json(run_params_json, video_id)

        return {
            'id': video_id,
            'title': run_params['title'],
            'url': run_params['replyStreamUrl'],
            'uploader': try_get(run_params, lambda x: x['followBar']['name'], compat_str),
            'timestamp': float_or_none(try_get(run_params, lambda x: x['followBar']['createTime']) / 1000),
        }
