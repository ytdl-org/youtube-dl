# encoding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    parse_iso8601,
    float_or_none,
    int_or_none,
)


class XboxClipsIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?xboxclips\.com/video\.php\?.*vid=(?P<id>[\w-]{36})'
    _TEST = {
        'url': 'https://xboxclips.com/video.php?uid=2533274823424419&gamertag=Iabdulelah&vid=074a69a9-5faf-46aa-b93b-9909c1720325',
        'md5': 'fbe1ec805e920aeb8eced3c3e657df5d',
        'info_dict': {
            'id': '074a69a9-5faf-46aa-b93b-9909c1720325',
            'ext': 'mp4',
            'title': 'Iabdulelah playing Upload Studio',
            'filesize_approx': 28101836.8,
            'timestamp': 1407388500,
            'upload_date': '20140807',
            'duration': 56,
        }
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')

        webpage = self._download_webpage(url, video_id)

        video_url = self._html_search_regex(
            r'>Link: <a href="([^"]+)">', webpage, 'video URL')
        title = self._html_search_regex(
            r'<title>XboxClips \| ([^<]+)</title>', webpage, 'title')
        timestamp = parse_iso8601(self._html_search_regex(
            r'>Recorded: ([^<]+)<', webpage, 'upload date', fatal=False))
        filesize = float_or_none(self._html_search_regex(
            r'>Size: ([\d\.]+)MB<', webpage, 'file size', fatal=False), invscale=1024 * 1024)
        duration = int_or_none(self._html_search_regex(
            r'>Duration: (\d+) Seconds<', webpage, 'duration', fatal=False))
        view_count = int_or_none(self._html_search_regex(
            r'>Views: (\d+)<', webpage, 'view count', fatal=False))

        return {
            'id': video_id,
            'url': video_url,
            'title': title,
            'timestamp': timestamp,
            'filesize_approx': filesize,
            'duration': duration,
            'view_count': view_count,
        }
