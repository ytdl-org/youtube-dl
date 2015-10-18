# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import parse_duration


class Canalc2IE(InfoExtractor):
    IE_NAME = 'canalc2.tv'
    _VALID_URL = r'https?://(?:www\.)?canalc2\.tv/video/(?P<id>\d+)'

    _TEST = {
        'url': 'http://www.canalc2.tv/video/12163',
        'md5': '060158428b650f896c542dfbb3d6487f',
        'info_dict': {
            'id': '12163',
            'ext': 'flv',
            'title': 'Terrasses du Numérique',
            'duration': 122,
        },
        'params': {
            'skip_download': True,  # Requires rtmpdump
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)
        video_url = self._search_regex(
            r'jwplayer\((["\'])Player\1\)\.setup\({[^}]*file\s*:\s*(["\'])(?P<file>.+?)\2',
            webpage, 'video_url', group='file')
        formats = [{'url': video_url}]
        if video_url.startswith('rtmp://'):
            rtmp = re.search(r'^(?P<url>rtmp://[^/]+/(?P<app>.+/))(?P<play_path>mp4:.+)$', video_url)
            formats[0].update({
                'url': rtmp.group('url'),
                'ext': 'flv',
                'app': rtmp.group('app'),
                'play_path': rtmp.group('play_path'),
                'page_url': url,
            })

        title = self._html_search_regex(
            r'(?s)class="[^"]*col_description[^"]*">.*?<h3>(.*?)</h3>', webpage, 'title')
        duration = parse_duration(self._search_regex(
            r'id=["\']video_duree["\'][^>]*>([^<]+)',
            webpage, 'duration', fatal=False))

        return {
            'id': video_id,
            'title': title,
            'duration': duration,
            'formats': formats,
        }
