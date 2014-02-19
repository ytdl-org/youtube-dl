# coding: utf-8
from __future__ import unicode_literals

import os.path
import re

from .common import InfoExtractor


class DropboxIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?dropbox[.]com/s/(?P<id>[a-zA-Z0-9]{15})/(?P<title>[^?#]*)'
    _TEST = {
        'url': 'https://www.dropbox.com/s/0qr9sai2veej4f8/THE_DOCTOR_GAMES.mp4',
        'md5': '8ae17c51172fb7f93bdd6a214cc8c896',
        'info_dict': {
            'id': '0qr9sai2veej4f8',
            'ext': 'mp4',
            'title': 'THE_DOCTOR_GAMES'
        }
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')
        title = os.path.splitext(mobj.group('title'))[0]
        video_url = url + '?dl=1'

        return {
            'id': video_id,
            'title': title,
            'url': video_url,
        }
