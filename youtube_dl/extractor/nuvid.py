from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    parse_duration,
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
            'age_limit': 18,
        }
    }

        def _real_extract(self, url):
        video_id = self._match_id(url)

        page_url = 'https://m.nuvid.com/video/%s' % video_id
        webpage = self._download_webpage(
            page_url, video_id, 'Downloading video page')

        video_hash_re = r'(?s)<(?:video|audio).+data-video_hash="(?P<video_hash>[^"]+)[^>]*(?:>)',
        hash_time_re = r'(?s)<(?:video|audio).+data-hash_time="(?P<hash_time>[^"]+)[^>]*(?:>)',
        video_hash = self._html_search_regex(video_hash_re, webpage, 'video_hash')
        hash_time = self._html_search_regex(hash_time_re, webpage, 'hash_time')

        query = {'video_hash': video_hash, 'hash_time': hash_time, 'video_id': video_id}
        player_source = self._download_json('https://m.nuvid.com/player_config', video_id, query=query)
        mp4_video_url = player_source['source']

        formats = [{
            'url': mp4_video_url
        }]

        title = self._html_search_regex(
            [r'<div class="[^"]+" title="([^"]+)" id="video_area">',
             r'<div class="thumb-holder video">\s*<h5[^>]*>([^<]+)</h5>',
             r'<span[^>]+class="title_thumb">([^<]+)</span>'], webpage, 'title').strip()
        thumbnails = [
            {
                'url': thumb_url,
            } for thumb_url in re.findall(r'<img src="([^"]+)" alt="" />', webpage)
        ]
        thumbnail = thumbnails[0]['url'] if thumbnails else None
        duration = parse_duration(self._html_search_regex(
            [r'<i class="fa fa-clock-o"></i>\s*(\d{2}:\d{2})',
             r'<span[^>]+class="view_time">([^<]+)</span>'], webpage, 'duration', fatal=False))

        return {
            'id': video_id,
            'title': title,
            'thumbnails': thumbnails,
            'thumbnail': thumbnail,
            'duration': duration,
            'age_limit': 18,
            'formats': formats,
        }
