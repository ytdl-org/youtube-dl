# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from datetime import datetime


class AliExpressLiveIE(InfoExtractor):

    _VALID_URL = r'https?://live\.aliexpress\.com/live/(?P<id>[0-9]{16})'
    _TEST = {
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
    }

    def _real_extract(self, url):
        vid_id = str(self._match_id(url))
        page = self._download_webpage(url, self._match_id(url)).replace('\n', '')
        # runParams is a variable which contains information about the stream
        run_params_json = self._search_regex(r'runParams = ([^<]+)[\s+]var [a-z]+', page, 'runParams')
        run_params = self._parse_json(run_params_json, vid_id)

        # the given unix timestamp contains 000 at the end, so we have to strip it off by dividing it with 1000
        upload_date = datetime.fromtimestamp(run_params.get('followBar').get('createTime') / 1000).strftime('%Y%m%d')

        return {
            'id': vid_id,
            'title': run_params['title'],
            'url': run_params['replyStreamUrl'],
            'uploader': run_params.get('followBar').get('name'),
            'upload_date': upload_date,
            'is_live': True,
        }
