# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import float_or_none


class CCTVIE(InfoExtractor):
    _VALID_URL = r'''(?x)https?://(?:.+?\.)?
        (?:
            cctv\.(?:com|cn)|
            cntv\.cn
        )/
        (?:
            video/[^/]+/(?P<id>[0-9a-f]{32})|
            \d{4}/\d{2}/\d{2}/(?P<display_id>VID[0-9A-Za-z]+)
        )'''
    _TESTS = [{
        'url': 'http://english.cntv.cn/2016/09/03/VIDEhnkB5y9AgHyIEVphCEz1160903.shtml',
        'md5': '819c7b49fc3927d529fb4cd555621823',
        'info_dict': {
            'id': '454368eb19ad44a1925bf1eb96140a61',
            'ext': 'mp4',
            'title': 'Portrait of Real Current Life 09/03/2016 Modern Inventors Part 1',
        }
    }, {
        'url': 'http://tv.cctv.com/2016/09/07/VIDE5C1FnlX5bUywlrjhxXOV160907.shtml',
        'only_matching': True,
    }, {
        'url': 'http://tv.cntv.cn/video/C39296/95cfac44cabd3ddc4a9438780a4e5c44',
        'only_matching': True
    }]

    def _real_extract(self, url):
        video_id, display_id = re.match(self._VALID_URL, url).groups()
        if not video_id:
            webpage = self._download_webpage(url, display_id)
            video_id = self._search_regex(
                r'(?:fo\.addVariable\("videoCenterId",\s*|guid\s*=\s*)"([0-9a-f]{32})',
                webpage, 'video_id')
        api_data = self._download_json(
            'http://vdn.apps.cntv.cn/api/getHttpVideoInfo.do?pid=' + video_id, video_id)
        m3u8_url = re.sub(r'maxbr=\d+&?', '', api_data['hls_url'])

        return {
            'id': video_id,
            'title': api_data['title'],
            'formats': self._extract_m3u8_formats(
                m3u8_url, video_id, 'mp4', 'm3u8_native', fatal=False),
            'duration': float_or_none(api_data.get('video', {}).get('totalLength')),
        }
