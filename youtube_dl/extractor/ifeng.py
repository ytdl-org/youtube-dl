# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor

from ..utils import (
    ExtractorError,
    unified_strdate,
)


class IFengIE(InfoExtractor):
    _VALID_URL = r'https?://(?:v\.)?ifeng\.com/video_(?P<id>\d+)\.shtml'

    _TEST = {
        'url': 'http://v.ifeng.com/video_11129877.shtml',
        'md5': '6cdca783b34bd31a678f418f4ff60816',
        'info_dict': {
            'id': '11129877',
            'ext': 'mp4',
            'title': '能自我修复的玻璃，手机用上它再也不怕碎屏了！',
            'description': 'md5:03a4d6c8c5ac7140b0cb085309fa8992',
            'timestamp': 1515675654,
            'upload_date': '20180111',
        }
    }

    def _report_error(self, result):
        if 'message' in result:
            raise ExtractorError('%s said: %s' % (self.IE_NAME, result['message']), expected=True)
        elif 'code' in result:
            raise ExtractorError('%s returns error %d' % (self.IE_NAME, result['code']), expected=True)
        else:
            raise ExtractorError('Can\'t extract Bangumi episode ID')

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        title = self._html_search_regex(
            r'"name": "(?P<value>(.+?))"',
            webpage, 'title', group='value')
        video_url = self._html_search_regex(
            r'"videoPlayUrl": "(?P<value>(.+?))"',
            webpage, 'url', group='value')

        if not video_url:
            self._report_error(title)

        thumbnail = self._html_search_regex(
            r'"videoLargePoster": "(?P<value>(.+?))"',
            webpage, 'thumbnail', group='value', fatal=False)
        uploader = self._html_search_regex(
            r'"columnName":"(?P<value>(.+?))"',
            webpage, 'uploader', group='value', fatal=False)
        duration = self._html_search_regex(
            r'"duration": "(?P<value>(.+?))"',
            webpage, 'duration', group='value', fatal=False)
        upload_date = unified_strdate(self._html_search_regex(
            r'"createdate": "(?P<value>(.+?))"',
            webpage, 'createdate', group='value', fatal=False))

        return {
            'id': video_id,
            'title': title,
            'duration': int(duration),
            'uploader': uploader,
            'upload_date': upload_date,
            'url': video_url,
            'thumbnail': thumbnail
        }
