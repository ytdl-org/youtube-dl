# coding: utf-8
from __future__ import unicode_literals
import re
import datetime

from .common import InfoExtractor


class TeleTaskIE(InfoExtractor):
    _VALID_URL = r'http?://(?:www\.)?tele-task\.de/archive/video/html5/(?P<id>[0-9]+)/'
    _TEST = {
        'url': 'http://www.tele-task.de/archive/video/html5/26168/',
        'info_dict': {
            'title': 'Duplicate Detection',
        },
        'playlist': [{
            'md5': '290ef69fb2792e481169c3958dbfbd57',
            'info_dict': {
                'title': 'Duplicate Detection',
                'upload_date': '20141218',
                'id': 'speaker_26168',
                'ext': 'mp4',
            }
        },
            {
            'md5': 'e1e7218c5f0e4790015a437fcf6c71b4',
            'info_dict': {
                'title': 'Duplicate Detection',
                'upload_date': '20141218',
                'id': 'slides_26168',
                'ext': 'mp4',
            }
        }]
    }

    def _real_extract(self, url):
        lecture_id = self._match_id(url)
        webpage = self._download_webpage(url, lecture_id)

        title = self._html_search_regex(
            r'itemprop="name">([^"]+)</a>', webpage, 'title')
        url_speaker = self._html_search_regex(
            r'class="speaker".*?src="([^"]+)"', webpage, 'video_url_speaker', flags=re.DOTALL)
        url_slides = self._html_search_regex(
            r'class="slides".*?src="([^"]+)"', webpage, 'video_url_slides', flags=re.DOTALL)
        date = self._html_search_regex(
            r'<td class="label">Date:</td><td>([^"]+)</td>', webpage, 'date')
        date = datetime.datetime.strptime(date, '%d.%m.%Y').strftime('%Y%m%d')

        entries = [{
            'title': title,
            'upload_date': date,
            'id': "speaker_"+lecture_id,
            'url': url_speaker,
        },
            {
            'title': title,
            'upload_date': date,
            'id': "slides_"+lecture_id,
            'url': url_slides}]

        return {
            '_type': "playlist",
            'id': lecture_id,
            'title': title,
            'entries': entries,
        }
