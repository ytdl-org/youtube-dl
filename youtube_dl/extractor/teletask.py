# coding: utf-8
from __future__ import unicode_literals

import re 
import datetime

from .common import InfoExtractor


class TeleTaskIE(InfoExtractor):
    _VALID_URL = r'http?://(?:www\.)?tele-task\.de/archive/video/html5/(?P<id>[0-9]+)/'
    _TEST = {
        'url': 'http://www.tele-task.de/archive/video/html5/26168/', 
        'md5': 'TODO: md5 sum of the first 10241 bytes of the video file (use --test)',
        'info_dict': {
            'id': '26168',
            'ext': 'mp4',
            'title': 'Duplicate Detection',
            'thumbnail': 're:^https?://.*\.jpg$',
            'date': '20141218',
            # TODO more properties, either as:
            # * A value
            # * MD5 checksum; start the string with md5:
            # * A regular expression; start the string with re:
            # * Any Python type (for example int or float)
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)
        
        lecture_url = self._html_search_regex(
                    r'href="([^"]+)" itemprop="name">', webpage, 'title')
        lecture_id = re.search("([0-9]+)/",lecture_url).group(1)
        overview_page = self._download_webpage("http://www.tele-task.de" + lecture_url, 
            lecture_id)
        
        title = self._html_search_regex(
            r'itemprop="name">([^"]+)</a>', webpage, 'title')
        url = self._html_search_regex(
            r'class="speaker".*?src="([^"]+)"', webpage, 'video_url', flags=re.DOTALL)
        description = self._html_search_regex(
            r'Description of the series:</p>([^"]+)</div>', overview_page, 
            'description',flags=re.DOTALL)
        
        date = self._html_search_regex(
            r'<td class="label">Date:</td><td>([^"]+)</td>', webpage, 'date')
        date = datetime.datetime.strptime(date, '%d.%m.%Y').strftime('%Y%m%d')

        

        return {
            'id': video_id,
            'title': title,
            'description': description,
            'url': url,
            'upload_date': date,
        }