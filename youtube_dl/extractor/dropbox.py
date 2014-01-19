# coding: utf-8
from __future__ import unicode_literals

import os.path
import re

from .common import InfoExtractor


class DropboxIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?dropbox[.]com/s/(?P<id>[a-zA-Z0-9]{15})/(?P<title>[^?#]*)'
    _TEST = {
        'url': 'https://www.dropbox.com/s/mcnzehi9wo55th4/20131219_085616.mp4',
        'file': 'mcnzehi9wo55th4.mp4',
        'md5': 'f6d65b1b326e82fd7ab7720bea3dacae',
        'info_dict': {
            'title': '20131219_085616'
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
