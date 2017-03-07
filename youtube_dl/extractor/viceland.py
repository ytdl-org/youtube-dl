# coding: utf-8
from __future__ import unicode_literals

from .vice import ViceBaseIE


class VicelandIE(ViceBaseIE):
    _VALID_URL = r'https?://(?:www\.)?viceland\.com/[^/]+/video/[^/]+/(?P<id>[a-f0-9]+)'
    _TEST = {
        'url': 'https://www.viceland.com/en_us/video/trapped/588a70d0dba8a16007de7316',
        'info_dict': {
            'id': '588a70d0dba8a16007de7316',
            'ext': 'mp4',
            'title': 'TRAPPED (Series Trailer)',
            'description': 'md5:7a8e95c2b6cd86461502a2845e581ccf',
            'age_limit': 14,
            'timestamp': 1485474122,
            'upload_date': '20170126',
            'uploader_id': '57a204098cb727dec794c6a3',
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
