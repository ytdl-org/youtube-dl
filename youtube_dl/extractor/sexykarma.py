# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    unified_strdate,
    parse_duration,
    int_or_none,
)


class SexyKarmaIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?sexykarma\.com/gonewild/video/(?P<display_id>[^/]+)-(?P<id>[a-zA-Z0-9]+)\.html'
    _TESTS = [{
        'url': 'http://www.sexykarma.com/gonewild/video/taking-a-quick-pee-yHI70cOyIHt.html',
        'md5': 'b9798e7d1ef1765116a8f516c8091dbd',
        'info_dict': {
            'id': 'yHI70cOyIHt',
            'display_id': 'taking-a-quick-pee',
            'ext': 'mp4',
            'title': 'Taking a quick pee.',
            'description': '',
            'thumbnail': 're:^https?://.*\.jpg$',
            'uploader': 'wildginger7',
            'upload_date': '20141007',
            'duration': 81,
            'view_count': int,
            'comment_count': int,
            'categories': list,
        }
    }, {
        'url': 'http://www.sexykarma.com/gonewild/video/pot-pixie-tribute-8Id6EZPbuHf.html',
        'md5': 'dd216c68d29b49b12842b9babe762a5d',
        'info_dict': {
            'id': '8Id6EZPbuHf',
            'display_id': 'pot-pixie-tribute',
            'ext': 'mp4',
            'title': 'pot_pixie tribute',
            'description': 'tribute',
            'thumbnail': 're:^https?://.*\.jpg$',
            'uploader': 'banffite',
            'upload_date': '20141013',
            'duration': 16,
            'view_count': int,
            'comment_count': int,
            'categories': list,
        }
    }]

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')
        display_id = mobj.group('display_id')

        webpage = self._download_webpage(url, display_id)

        video_url = self._html_search_regex(
            r'<p>Save this video to your computer: </p><p><a href="([^"]+)"',
            webpage, 'url')

        title = self._html_search_regex(
            r'<h2 class="he2"><span>(.*?)</span>',
            webpage, 'title')
        description = self._html_search_meta(
            'description', webpage, 'description', fatal=False, default='')
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

        categories = self._html_search_meta(
            'keywords', webpage, 'categories',
            fatal=False, default='').split(',')

        return {
            'id': video_id,
            'display_id': display_id,
            'url': video_url,
            'title': title,
            'description': description,
            'thumbnail': thumbnail,
            'uploader': uploader,
            'upload_date': upload_date,
            'duration': duration,
            'view_count': view_count,
            'comment_count': comment_count,
            'categories': categories,
        }
