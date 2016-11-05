# coding: utf-8
from __future__ import unicode_literals

from .vice import ViceBaseIE


class VicelandIE(ViceBaseIE):
    _VALID_URL = r'https?://(?:www\.)?viceland\.com/[^/]+/video/[^/]+/(?P<id>[a-f0-9]+)'
    _TEST = {
        'url': 'https://www.viceland.com/en_us/video/cyberwar-trailer/57608447973ee7705f6fbd4e',
        'info_dict': {
            'id': '57608447973ee7705f6fbd4e',
            'ext': 'mp4',
            'title': 'CYBERWAR (Trailer)',
            'description': 'Tapping into the geopolitics of hacking and surveillance, Ben Makuch travels the world to meet with hackers, government officials, and dissidents to investigate the ecosystem of cyberwarfare.',
            'age_limit': 14,
            'timestamp': 1466008539,
            'upload_date': '20160615',
            'uploader_id': '11',
            'uploader': 'Viceland',
        },
        'params': {
            # m3u8 download
            'skip_download': True,
        },
        'add_ie': ['UplynkPreplay'],
    }
    _PREPLAY_HOST = 'www.viceland'

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)
        return self._extract_preplay_video(url, webpage)
