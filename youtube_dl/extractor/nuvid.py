# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..compat import compat_str
from ..utils import (
    parse_duration,
    int_or_none,
    try_get,
    url_or_none,
)

import re


class NuvidIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www|m)\.nuvid\.com/video/(?P<id>[0-9]+)'
    _TESTS = [{
        'url': 'https://www.nuvid.com/video/6513023/italian-babe',
        'md5': '772d2f8288f3d3c5c45f7a41761c7844',
        'info_dict': {
            'id': '6513023',
            'ext': 'mp4',
            'title': 'italian babe',
            'format_id': '360p',
            'duration': 321.0,
            'age_limit': 18,
            'thumbnail': r're:https?://.+\.jpg',
            'thumbnails': list,
        }
    }, {
        'url': 'https://m.nuvid.com/video/6523263',
        'md5': 'ebd22ce8e47e1d9a4d0756a15c67da52',
        'info_dict': {
            'id': '6523263',
            'ext': 'mp4',
            'title': 'Slut brunette college student anal dorm',
            'format_id': '720p',
            'duration': 421.0,
            'age_limit': 18,
            'thumbnail': r're:https?://.+\.jpg',
            'thumbnails': list,
        }
    }, {
        'url': 'http://m.nuvid.com/video/6415801/',
        'md5': '638d5ececb138d5753593f751ae3f697',
        'info_dict': {
            'id': '6415801',
            'ext': 'mp4',
            'title': 'My best friend wanted to fuck my wife for a long time',
            'format_id': '720p',
            'duration': 1882,
            'age_limit': 18,
            'thumbnail': r're:https?://.+\.jpg',
            'thumbnails': list,
        }
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)

        qualities = {
            'lq': '360p',
            'hq': '720p',
        }

        json_url = 'https://www.nuvid.com/player_config_json/?vid={video_id}&aid=0&domain_id=0&embed=0&check_speed=0'.format(**locals())
        video_data = self._download_json(
            json_url, video_id, headers={
                'Accept': 'application/json, text/javascript, */*; q = 0.01',
                'Content-Type': 'application/x-www-form-urlencoded; charset=utf-8',
            }) or {}

        # nice to have, not required
        webpage = self._download_webpage(
            'http://m.nuvid.com/video/%s' % (video_id, ),
            video_id, 'Downloading video page', fatal=False) or ''

        title = (
            try_get(video_data, lambda x: x['title'], compat_str)
            or self._html_search_regex(
                (r'''<span\s[^>]*?\btitle\s*=\s*(?P<q>"|'|\b)(?P<title>[^"]+)(?P=q)\s*>''',
                 r'''<div\s[^>]*?\bclass\s*=\s*(?P<q>"|'|\b)thumb-holder video(?P=q)>\s*<h5\b[^>]*>(?P<title>[^<]+)</h5''',
                 r'''<span\s[^>]*?\bclass\s*=\s*(?P<q>"|'|\b)title_thumb(?P=q)>(?P<title>[^<]+)</span'''),
                webpage, 'title', group='title')).strip()

        formats = [{
            'url': source,
            'format_id': qualities.get(quality),
            'height': int_or_none(qualities.get(quality)[:-1]),
        } for quality, source in video_data.get('files').items() if source]

        self._check_formats(formats, video_id)
        self._sort_formats(formats)

        duration = parse_duration(video_data.get('duration') or video_data.get('duration_format'))
        thumbnails = [
            {'url': thumb_url, }
            for thumb_url in (
                url_or_none(src) for src in re.findall(
                    r'<div\s+class\s*=\s*"video-tmb-wrap"\s*>\s*<img\s+src\s*=\s*"([^"]+)"\s*/>',
                    webpage))
        ]

        return {
            'id': video_id,
            'formats': formats,
            'title': title,
            'thumbnail': url_or_none(video_data.get('poster')),
            'thumbnails': thumbnails,
            'duration': duration,
            'age_limit': 18,
        }
