# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor

from ..utils import (
    ExtractorError,
    unified_strdate,
    int_or_none
)
import re


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

        video_info = self._parse_json(self._html_search_regex(
            r'var videoinfo = (?P<value>({.+?}));',
            webpage, 'video_info', flags=re.DOTALL, group='value'), video_id)

        video_url = video_info.get('videoPlayUrl')

        if not video_url:
            self._report_error(video_url)

        formats = [
            {
                'url': video_url,
                'ext': video_url[video_url.rfind('.') + 1:],
            }
        ]
        self._sort_formats(formats)

        return {
            'id': video_id,
            'title': video_info.get('name'),
            'duration': int_or_none(video_info.get('duration')),
            'uploader': video_info.get('columnName'),
            'upload_date': unified_strdate(video_info.get('createdate')),
            'thumbnail': video_info.get('videoLargePoster'),
            'formats': formats,
        }
