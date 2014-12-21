# coding: utf-8
from __future__ import unicode_literals

import re 
import datetime

from .common import InfoExtractor


class TeleTaskIE(InfoExtractor):
    _VALID_URL = r'http?://(?:www\.)?tele-task\.de/archive/video/html5/(?P<id>[0-9]+)/'
    _TEST = {
        'url': 'http://www.tele-task.de/archive/video/html5/26168/', 
        'md5': '290ef69fb2792e481169c3958dbfbd57',
        'info_dict': {
            'id': '26168',
            'ext': 'mp4',
            'title': 'Duplicate Detection',
            'upload_date': '20141218',
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)
        
        title = self._html_search_regex(
            r'itemprop="name">([^"]+)</a>', webpage, 'title')
        url = self._html_search_regex(
            r'class="speaker".*?src="([^"]+)"', webpage, 'video_url', flags=re.DOTALL)
        
        date = self._html_search_regex(
            r'<td class="label">Date:</td><td>([^"]+)</td>', webpage, 'date')
        date = datetime.datetime.strptime(date, '%d.%m.%Y').strftime('%Y%m%d')

        

        return {
            'id': video_id,
            'title': title,
            'url': url,
            'upload_date': date,
        }