# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..compat import (
    compat_urllib_parse_unquote,
    compat_urllib_request,
)

class ImoocVideoIE(InfoExtractor):
    _VALID_URL = r'http://www.imooc.com/video/(?P<id>[0-9]+)'
    _TESTS = [
        {
        'url': 'http://www.imooc.com/video/6511',
        'md5': '756ca7b6e934aedee496e208f290bff3',
        'info_dict': {
            'id': '6511',
            'ext': 'mp4',
            'title': 'Bash变量与变量分类'}
    },
    {
        'url': 'http://www.imooc.com/video/5454',
        'md5': '1feb8b14a07f5272b400b271292cc1f6',
        'info_dict': {
            'id': '5454',
            'ext': 'mp4',
            'title': '网络环境查看命令',
        }
    }
    ]

    def _real_extract(self, url):
        video_id = self._match_id(url)

        json_url = 'http://www.imooc.com/course/ajaxmediainfo/?mid=%s&mode=flash' % video_id
        data = self._download_json(json_url, video_id, 'Downloading video formats')

        url = data['data']['result']['mpath'][0]

        title = data['data']['result']['name']

        return {
            'id': video_id,
            'title': title,
            'url': url
        }