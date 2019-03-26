# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
import re


class TvPleIE(InfoExtractor):
    _VALID_URL = r'https?://tvple.com/.+'
    _TEST = {
        'url': 'http://tvple.com/381843',
        'info_dict': {
            'id': '381843',
            'ext': 'mp4',
            'title': '티비플 &raquo; [팀 달캬] 마더즈 로자리오(Mother`s Rosario) 프로젝트 &raquo; 퍼가기',
        }
    }

    def _real_extract(self, url):
        video_id = re.findall('\d.+', url)
        webpage = self._download_webpage(url, video_id)
        title = re.findall(r'<title>(.+)<\/title>', webpage)
        api_request_url = re.findall(r'(http:\/\/api\.tvple\.com\/v1.*?)"', webpage)
        api_page = self._download_webpage(api_request_url[0], video_id)
        urlh = re.findall(r'(http:\/\/media.*?)"', api_page)
        return {
            'id': video_id[0],
            'title': title,
            'ext': 'mp4',
            'url': urlh[0]
        }
