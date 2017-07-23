# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor


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
        # runParams is a variable which contains information about the stream
        run_params_json = self._search_regex(r'runParams = ([^<]+)[\s+]var [a-z]+', page, 'runParams')
        run_params = self._parse_json(run_params_json, video_id)

        return {
            'id': video_id,
            'title': run_params['title'],
            'url': run_params['replyStreamUrl'],
            'uploader': run_params.get('followBar', {'name': None}).get('name'),
            # the given unix timestamp contains 000 at the end, so we have to strip it off by dividing it with 1000
            'timestamp': run_params.get('followBar', {'createTime': 0}).get('createTime', 0) / 1000,
        }
