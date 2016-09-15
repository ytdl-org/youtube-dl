# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..compat import compat_urlparse
from ..utils import (
    float_or_none,
    month_by_abbreviation,
    ExtractorError,
    get_element_by_attribute,
)


class YamIE(InfoExtractor):
    IE_DESC = '蕃薯藤yam天空部落'
    _VALID_URL = r'https?://mymedia\.yam\.com/m/(?P<id>\d+)'

    _TESTS = [{
        # An audio hosted on Yam
        'url': 'http://mymedia.yam.com/m/2283921',
        'md5': 'c011b8e262a52d5473d9c2e3c9963b9c',
        'info_dict': {
            'id': '2283921',
            'ext': 'mp3',
            'title': '發現 - 趙薇 京華煙雲主題曲',
            'description': '發現 - 趙薇 京華煙雲主題曲',
            'uploader_id': 'princekt',
            'upload_date': '20080807',
            'duration': 313.0,
        }
    }, {
        # An external video hosted on YouTube
        'url': 'http://mymedia.yam.com/m/3599430',
        'md5': '03127cf10d8f35d120a9e8e52e3b17c6',
        'info_dict': {
            'id': 'CNpEoQlrIgA',
            'ext': 'mp4',
            'upload_date': '20150306',
            'uploader': '新莊社大瑜伽社',
            'description': 'md5:11e2e405311633ace874f2e6226c8b17',
            'uploader_id': '2323agoy',
            'title': '20090412陽明山二子坪-1',
        },
        'skip': 'Video does not exist',
    }, {
        'url': 'http://mymedia.yam.com/m/3598173',
        'info_dict': {
            'id': '3598173',
            'ext': 'mp4',
        },
        'skip': 'cause Yam system error',
    }, {
        'url': 'http://mymedia.yam.com/m/3599437',
        'info_dict': {
            'id': '3599437',
            'ext': 'mp4',
        },
        'skip': 'invalid YouTube URL',
    }, {
        'url': 'http://mymedia.yam.com/m/2373534',
        'md5': '7ff74b91b7a817269d83796f8c5890b1',
        'info_dict': {
            'id': '2373534',
            'ext': 'mp3',
            'title': '林俊傑&蔡卓妍-小酒窩',
            'description': 'md5:904003395a0fcce6cfb25028ff468420',
            'upload_date': '20080928',
            'uploader_id': 'onliner2',
        }
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        page = self._download_webpage(url, video_id)

        # Check for errors
        system_msg = self._html_search_regex(
            r'系統訊息(?:<br>|\n|\r)*([^<>]+)<br>', page, 'system message',
            default=None)
        if system_msg:
            raise ExtractorError(system_msg, expected=True)

        # Is it hosted externally on YouTube?
        youtube_url = self._html_search_regex(
            r'<embed src="(http://www.youtube.com/[^"]+)"',
            page, 'YouTube url', default=None)
        if youtube_url:
            return self.url_result(youtube_url, 'Youtube')

        title = self._html_search_regex(
            r'<h1[^>]+class="heading"[^>]*>\s*(.+)\s*</h1>', page, 'title')

        api_page = self._download_webpage(
            'http://mymedia.yam.com/api/a/?pID=' + video_id, video_id,
            note='Downloading API page')
        api_result_obj = compat_urlparse.parse_qs(api_page)

        info_table = get_element_by_attribute('class', 'info', page)
        uploader_id = self._html_search_regex(
            r'<!-- 發表作者 -->：[\n ]+<a href="/([a-z0-9]+)"',
            info_table, 'uploader id', fatal=False)
        mobj = re.search(r'<!-- 發表於 -->(?P<mon>[A-Z][a-z]{2})\s+' +
                         r'(?P<day>\d{1,2}), (?P<year>\d{4})', page)
        if mobj:
            upload_date = '%s%02d%02d' % (
                mobj.group('year'),
                month_by_abbreviation(mobj.group('mon')),
                int(mobj.group('day')))
        else:
            upload_date = None
        duration = float_or_none(api_result_obj['totaltime'][0], scale=1000)

        return {
            'id': video_id,
            'url': api_result_obj['mp3file'][0],
            'title': title,
            'description': self._html_search_meta('description', page),
            'duration': duration,
            'uploader_id': uploader_id,
            'upload_date': upload_date,
        }
