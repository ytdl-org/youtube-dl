# coding: utf-8
from __future__ import unicode_literals

import re
from .common import InfoExtractor

from ..utils import (
    smuggle_url,
    update_url_query,
)

class EOnlineIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?eonline\.com/[a-z]{2}(?:/[a-z-]+){3}/[0-9]+/(?P<display_id>[a-z-]+)'
    _TEST = {
        'url': 'http://www.eonline.com/uk/shows/botched/videos/249184/transgender-woman-takes-a-trip-to-her-past',
        'md5': '1ca5b36c4337fde2b65207e0ad0c11c0',
        'info_dict': {
            'id': 'C872_ktn4Rgc',
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
        display_id = mobj.group('display_id')
        webpage = self._download_webpage(url, display_id)

        release_url = self._search_regex(r'"videoSourceUrl"\s*:\s*"(.+)"',
            webpage, 'ThePlatform ID')

        return {
            '_type': 'url_transparent', 
            'ie_key': 'ThePlatform',
            'url': smuggle_url(update_url_query(release_url, {'mbr': 'true', 'switch': 'http'}),
                {'force_smil_url': True}),
            'display_id': display_id,
        }
