# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import int_or_none

class HentaiHavenIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?hentaihaven\.org/(?P<id>[^/]+)'
    _TEST = {
        'url': 'http://hentaihaven.org/oideyo-shiritsu-yarimari-gakuen-episode-1-hd',
        'md5': 'd9e1ed0558c0c29267743c463c34e71b',
        'info_dict': {
            'id': 'oideyo-shiritsu-yarimari-gakuen-episode-1-hd',
            'title': 'Oideyo! Shiritsu Yarimari Gakuen – Episode 1',
            'ext': 'mp4',
            'age_limit': 18,
            'formats': [
                {
                    'url': 'http://hh.cx/files/34/[HH] Oideyo! Shiritsu Yarimari Gakuen - Episode 1 [DVD] [3FFC5997].mp4',
                    'ext': 'mp4',
                    'height': 720,
                },
                {
                    'url': 'http://hh.cx/files/04/[HH] Oideyo! Shiritsu Yarimari Gakuen - Episode 1 [SD].mp4',
                    'ext': 'mp4',
                    'height': 480,
                },
                {
                    'url': 'http://hh.cx/files/1a/[HH]direct_PID48840[SD].mp4',
                    'ext': 'mp4',
                    'height': 360,
                },
            ]
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)

        webpage = self._download_webpage(url, video_id)

        title = self._html_search_regex(
            r'<h1[^>]+class=(["\'])*entry-title\1*[^>]*>(?P<title>[^<]+)',
            webpage, 'title', group='title')

        btn_re = re.compile(r'(<a[^>]+class="btn"*[^>]+>)')
        res_re = re.compile(r'<span[^>]+class=["\']*text-white["\']*[^>]*>([^<]+)')
        
        formats = []
        for (btn, res) in zip(btn_re.findall(webpage), res_re.findall(webpage)):
            format_info = {}
            format_info['url'] = self._html_search_regex(
                r'<a[^>]+href=["\']([^"\']+)["\'][^>]+>',
                btn, 'href')
            format_info['ext'] = 'mp4'
            format_info['height'] = int_or_none(res[:-1])
            formats.append(format_info)

        return {
            'id': video_id,
            'title': title,
            'age_limit': 18,
            'formats': formats,
        }