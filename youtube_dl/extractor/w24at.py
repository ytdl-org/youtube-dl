# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor


class W24atIE(InfoExtractor):
    _VALID_URL = r'https://(?:www\.)?w24\.at/Video/.*/(?P<id>[0-9]+)'
    _TEST = {
        'url': 'https://www.w24.at/Video/Bewegung-macht-Spass-Folge-62-Kids-6/24828',
        'md5': '2cfa88aa93f7747a20567ca1ca4a9ab7',
        'info_dict': {
            'id': '24828',
            'ext': 'mp4',
            'title': 'Bewegung macht Spaß! - Folge 62: Kids 6 - W24',
            'description': 'Stefans Ziel ist es Kindern auch hinter den Bildschirmen zur Bewegung und zum Denksport zu animieren und das ganze mit Spaß und Köpfchen zu verbinden.'
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)
        media_server = self._html_search_regex(r'var\s*mediaServer\s*=\s*\{.*"vod"\s*:\s*"([^"]+)"',
                                               webpage, "vod", "ms02.w24.at")
        m3u8_path = self._html_search_regex(r"src:.*\+ '([^']+)'.*type:'application/x-mpegURL'",
                                            webpage, "video")
        return {
            'id': video_id,
            'title': self._og_search_title(webpage),
            'description': self._og_search_description(webpage),
            'formats': self._extract_m3u8_formats("https://%s%s" % (media_server, m3u8_path), video_id, 'mp4'),
            'extension': 'mp4'
        }
