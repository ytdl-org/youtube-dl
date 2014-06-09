from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    parse_duration,
    unified_strdate,
    compat_urllib_request,
)


class NuvidIE(InfoExtractor):
    _VALID_URL = r'^https?://(?:www|m)\.nuvid\.com/video/(?P<id>[0-9]+)'
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
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')

        formats = []

        for dwnld_speed, format_id in [(0, '3gp'), (5, 'mp4')]:
            request = compat_urllib_request.Request(
                'http://m.nuvid.com/play/%s' % video_id)
            request.add_header('Cookie', 'skip_download_page=1; dwnld_speed=%d; adv_show=1' % dwnld_speed)
            webpage = self._download_webpage(
                request, video_id, 'Downloading %s page' % format_id)
            video_url = self._html_search_regex(
                r'<a href="([^"]+)"\s*>Continue to watch video', webpage, '%s video URL' % format_id, fatal=False)
            if not video_url:
                continue
            formats.append({
                'url': video_url,
                'format_id': format_id,
            })

        webpage = self._download_webpage(
            'http://m.nuvid.com/video/%s' % video_id, video_id, 'Downloading video page')
        title = self._html_search_regex(
            r'<div class="title">\s+<h2[^>]*>([^<]+)</h2>', webpage, 'title').strip()
        thumbnail = self._html_search_regex(
            r'href="(/thumbs/[^"]+)"[^>]*data-link_type="thumbs"',
            webpage, 'thumbnail URL', fatal=False)
        duration = parse_duration(self._html_search_regex(
            r'Length:\s*<span>(\d{2}:\d{2})</span>',webpage, 'duration', fatal=False))
        upload_date = unified_strdate(self._html_search_regex(
            r'Added:\s*<span>(\d{4}-\d{2}-\d{2})</span>', webpage, 'upload date', fatal=False))

        return {
            'id': video_id,
            'title': title,
            'thumbnail': 'http://m.nuvid.com%s' % thumbnail,
            'duration': duration,
            'upload_date': upload_date,
            'age_limit': 18,
            'formats': formats,
        }