# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    unified_strdate,
    parse_duration,
    int_or_none,
)


class WatchIndianPornIE(InfoExtractor):
    IE_DESC = 'Watch Indian Porn'
    _VALID_URL = r'https?://(?:www\.)?watchindianporn\.net/(?:[^/]+/)*video/(?P<display_id>[^/]+)-(?P<id>[a-zA-Z0-9]+)\.html'
    _TEST = {
        'url': 'http://www.watchindianporn.net/video/hot-milf-from-kerala-shows-off-her-gorgeous-large-breasts-on-camera-RZa2avywNPa.html',
        'md5': '249589a164dde236ec65832bfce17440',
        'info_dict': {
            'id': 'RZa2avywNPa',
            'display_id': 'hot-milf-from-kerala-shows-off-her-gorgeous-large-breasts-on-camera',
            'ext': 'mp4',
            'title': 'Hot milf from kerala shows off her gorgeous large breasts on camera',
            'thumbnail': r're:^https?://.*\.jpg$',
            'uploader': 'LoveJay',
            'upload_date': '20160428',
            'duration': 226,
            'view_count': int,
            'comment_count': int,
            'categories': list,
            'age_limit': 18,
        }
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')
        display_id = mobj.group('display_id')

        webpage = self._download_webpage(url, display_id)

        video_url = self._html_search_regex(
            r"url: escape\('([^']+)'\)", webpage, 'url')

        title = self._html_search_regex(
            r'<h2 class="he2"><span>(.*?)</span>',
            webpage, 'title')
        thumbnail = self._html_search_regex(
            r'<span id="container"><img\s+src="([^"]+)"',
            webpage, 'thumbnail', fatal=False)

        uploader = self._html_search_regex(
            r'class="aupa">\s*(.*?)</a>',
            webpage, 'uploader')
        upload_date = unified_strdate(self._html_search_regex(
            r'Added: <strong>(.+?)</strong>', webpage, 'upload date', fatal=False))

        duration = parse_duration(self._search_regex(
            r'<td>Time:\s*</td>\s*<td align="right"><span>\s*(.+?)\s*</span>',
            webpage, 'duration', fatal=False))

        view_count = int_or_none(self._search_regex(
            r'<td>Views:\s*</td>\s*<td align="right"><span>\s*(\d+)\s*</span>',
            webpage, 'view count', fatal=False))
        comment_count = int_or_none(self._search_regex(
            r'<td>Comments:\s*</td>\s*<td align="right"><span>\s*(\d+)\s*</span>',
            webpage, 'comment count', fatal=False))

        categories = re.findall(
            r'<a href="[^"]+/search/video/desi"><span>([^<]+)</span></a>',
            webpage)

        return {
            'id': video_id,
            'display_id': display_id,
            'url': video_url,
            'http_headers': {
                'Referer': url,
            },
            'title': title,
            'thumbnail': thumbnail,
            'uploader': uploader,
            'upload_date': upload_date,
            'duration': duration,
            'view_count': view_count,
            'comment_count': comment_count,
            'categories': categories,
            'age_limit': 18,
        }
