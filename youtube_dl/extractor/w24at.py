# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor


class W24atIE(InfoExtractor):
    _VALID_URL = r'https://(?:www\.)?w24\.at/Video/.*/(?P<id>[0-9]+)'
    _TEST = {
        'url': 'https://www.w24.at/Video/Bewegung-macht-Spass-Folge-62-Kids-6/24828',
        'md5': '16e6f1c5d4a0d54d420e3d9d122660a1',
        'info_dict': {
            'id': '24828',
            'ext': 'mp4',
            'title': 'Bewegung macht Spaß! - Folge 62: Kids 6',
            'description': 'Stefans Ziel ist es Kindern auch hinter den Bildschirmen zur Bewegung und zum Denksport zu animieren und das ganze mit Spaß und Köpfchen zu verbinden.',
            'thumbnail': r're:.*\.jpg$',
            'uploader': 'W24'
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)
        media_server = self._html_search_regex(r'var\s*mediaServer\s*=\s*\{.*"vod"\s*:\s*"([^"]+)"',
                                               webpage, "vod", "ms02.w24.at")
        mp4_path = self._html_search_regex(r"src:.*\+ '([^']+)'.*type:'video/mp4'",
                                           webpage, "mp4_path")
        m3u8_path = self._html_search_regex(r"src:.*\+ '([^']+)'.*type:'application/x-mpegURL'",
                                            webpage, "m3u8_path")
        formats = []
        if mp4_path:
            formats.append({'url': "https://%s%s" % (media_server, mp4_path), 'ext': 'mp4'})
        formats.extend(self._extract_m3u8_formats("https://%s%s" % (media_server, m3u8_path), video_id, ext='mp4'))
        self._sort_formats(formats)
        return {
            'id': video_id,
            'title': re.sub(r'\s+-\sW24\s*$', '', self._og_search_title(webpage)),
            'description': self._og_search_description(webpage),
            'formats': formats,
            'thumbnail': self._og_search_thumbnail(webpage),
            'uploader': self._og_search_property('site_name', webpage, fatal=False),
        }
