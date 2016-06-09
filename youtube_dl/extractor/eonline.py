# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    smuggle_url,
    update_url_query,
)

class EOnlineIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?eonline\.com/[a-z]{2}(?:/[a-z-]+){3}/(?P<id>[0-9]+)/(?P<display_id>[a-z-]+)'
    _TEST = {
        'url': 'http://www.eonline.com/uk/shows/botched/videos/249184/transgender-woman-takes-a-trip-to-her-past',
        'md5': '1ca5b36c4337fde2b65207e0ad0c11c0',
        'info_dict': {
            'id': '249184',
            'ext': 'mp4',
            'title': 'Transgender Woman Takes a Trip to Her Past',
            'description': 'md5:621feda5e84d5d4a29f4cc26faa33d24',
            'timestamp': 1464364800,
            'upload_date': '20160527',
            'uploader': 'NBCU-E',
        }
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id, display_id = mobj.group('id', 'display_id')
        webpage = self._download_webpage(url, display_id)

        data = self._parse_json(self._search_regex(
            r'evideo.videos.detail\s*=\s*(\[\s*\{[^\]]+]);',
                webpage, 'JSON data'), display_id)

        for entry in data:
            if entry['id'] == video_id:
                release_url = entry['videoSourceUrl']

        return {
            '_type': 'url_transparent',
            'ie_key': 'ThePlatform',
            'url': smuggle_url(update_url_query(release_url, {'mbr': True, 'switch': 'http'}), {'force_smil_url': True}),
            'id': video_id,
            'display_id': display_id,
        }
