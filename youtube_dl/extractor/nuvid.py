from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    parse_duration,
    sanitized_Request,
    unified_strdate,
)


class NuvidIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www|m)\.nuvid\.com/video/(?P<id>[0-9]+)'
    _TEST = {
        'url': 'http://m.nuvid.com/video/1310741/',
        'md5': 'eab207b7ac4fccfb4e23c86201f11277',
        'info_dict': {
            'id': '1310741',
            'ext': 'mp4',
            'title': 'Horny babes show their awesome bodeis and',
            'duration': 129,
            'upload_date': '20140508',
            'age_limit': 18,
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)

        formats = []

        for dwnld_speed, format_id in [(0, '3gp'), (5, 'mp4')]:
            request = sanitized_Request(
                'http://m.nuvid.com/play/%s' % video_id)
            request.add_header('Cookie', 'skip_download_page=1; dwnld_speed=%d; adv_show=1' % dwnld_speed)
            webpage = self._download_webpage(
                request, video_id, 'Downloading %s page' % format_id)
            video_url = self._html_search_regex(
                r'<a\s+href="([^"]+)"\s+class="b_link">', webpage, '%s video URL' % format_id, fatal=False)
            if not video_url:
                continue
            formats.append({
                'url': video_url,
                'format_id': format_id,
            })

        webpage = self._download_webpage(
            'http://m.nuvid.com/video/%s' % video_id, video_id, 'Downloading video page')
        title = self._html_search_regex(
            [r'<span title="([^"]+)">',
             r'<div class="thumb-holder video">\s*<h5[^>]*>([^<]+)</h5>'], webpage, 'title').strip()
        thumbnails = [
            {
                'url': thumb_url,
            } for thumb_url in re.findall(r'<img src="([^"]+)" alt="" />', webpage)
        ]
        thumbnail = thumbnails[0]['url'] if thumbnails else None
        duration = parse_duration(self._html_search_regex(
            r'<i class="fa fa-clock-o"></i>\s*(\d{2}:\d{2})', webpage, 'duration', fatal=False))
        upload_date = unified_strdate(self._html_search_regex(
            r'<i class="fa fa-user"></i>\s*(\d{4}-\d{2}-\d{2})', webpage, 'upload date', fatal=False))

        return {
            'id': video_id,
            'title': title,
            'thumbnails': thumbnails,
            'thumbnail': thumbnail,
            'duration': duration,
            'upload_date': upload_date,
            'age_limit': 18,
            'formats': formats,
        }
