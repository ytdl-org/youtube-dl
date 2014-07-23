# coding: utf-8
from __future__ import unicode_literals

import os.path
import re

from .common import InfoExtractor
from ..utils import compat_urllib_parse_unquote


class DropboxIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?dropbox[.]com/s/(?P<id>[a-zA-Z0-9]{15})/(?P<title>[^?#]*)'
    _TEST = {
        'url': 'https://www.dropbox.com/s/nelirfsxnmcfbfh/youtube-dl%20test%20video%20%27%C3%A4%22BaW_jenozKc.mp4',
        'md5': '8a3d905427a6951ccb9eb292f154530b',
        'info_dict': {
            'id': 'nelirfsxnmcfbfh',
            'ext': 'mp4',
            'title': 'youtube-dl test video \'ä"BaW_jenozKc'
        }
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')
        fn = compat_urllib_parse_unquote(mobj.group('title'))
        title = os.path.splitext(fn)[0]
        video_url = url + '?dl=1'

        return {
            'id': video_id,
            'title': title,
            'url': video_url,
        }
