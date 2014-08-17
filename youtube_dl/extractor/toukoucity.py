# coding: utf-8
from __future__ import unicode_literals

import re
try:
    # Python 3 urllib
    from urllib.request import urlopen
except ImportError:
    # Fall back to Python 2's urllib2
    from urllib2 import urlopen

from .common import InfoExtractor
from ..utils import (
    unified_strdate,
)

class ToukouCityIE(InfoExtractor):
    IE_NAME = 'ToukouCity'
    IE_DESC = '無料アダルトビデオが豊富なカテゴリーで楽しめる'
    _VALID_URL = r'https?://(?:www\.)?toukoucity\.to/video/(?P<id>[\w\d]+)/?'
    _TEST = {
        'url': 'http://toukoucity.to/video/igy3nBwTEb/',
        'md5': 'd36db92d7a2034312ab692ba97f216ab',
        'info_dict': {
            'id': 'igy3nBwTEb',
            'filesize': 366450899,
            'ext': 'mp4',
            'title': u'ドラえもん',
            'description': u'のび太のブリキの迷宮（ラビリンス）',
            'thumbnail': 'http://img.toukoucity.to/igy3nBwTEb/thumbnail_12.jpg',
            'upload_date': '20140805',
        }
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')

        self.report_extraction(video_id)

        webpage = self._download_webpage(url, video_id)
        title = self._html_search_regex(r'<h2 class="titles">(.+?)</h2>', webpage, u'title')
        video_url = self._search_regex(r'so\.addVariable\(\'file\',\'(.+?\.mp4)\'\)', webpage, u'video_url')
        thumbnail = self._search_regex(r'so\.addVariable\(\'image\',\'(.+?)\'\)', webpage, u'thumbnail')
        upload_date = unified_strdate(self._search_regex(r'<span class="gray_s">(.+?)</span>', webpage, u'upload_date'))
        extension = video_url.split(".")[-1]
        view_count = self._html_search_regex(r'<span class="load">(.+?)</span>', webpage, u'view_count')
        player_url = self._search_regex(r'SWFObject\(\'(.+?)\'.+?\)', webpage, u'player_url')
        description = self._search_regex(r'<p class="dot">(.+?)</p>', webpage, u'description')
        filesize = int(urlopen(video_url).headers["Content-Length"])

        return {
            'id': video_id,
            'title': title,
            'url': video_url,
            'thumbnail': thumbnail,
            'upload_date': upload_date,
            'ext': extension,
            'player_url': player_url,
            'description': description,
            'view_count': view_count,
            'webpage_url': url,
            'filesize': filesize,
        }