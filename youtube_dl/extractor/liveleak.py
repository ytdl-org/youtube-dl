from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
)


class LiveLeakIE(InfoExtractor):
    _VALID_URL = r'^(?:http://)?(?:\w+\.)?liveleak\.com/view\?(?:.*?)i=(?P<video_id>[\w_]+)(?:.*)'
    _TEST = {
        'url': 'http://www.liveleak.com/view?i=757_1364311680',
        'file': '757_1364311680.mp4',
        'md5': '0813c2430bea7a46bf13acf3406992f4',
        'info_dict': {
            'description': 'extremely bad day for this guy..!',
            'uploader': 'ljfriel2',
            'title': 'Most unlucky car accident'
        }
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)

        video_id = mobj.group('video_id')
        webpage = self._download_webpage(url, video_id)
        video_url = self._search_regex(
            r'file: "(.*?)",', webpage, 'video URL')

        video_title = self._og_search_title(webpage).replace('LiveLeak.com -', '').strip()
        video_description = self._og_search_description(webpage)
        video_uploader = self._html_search_regex(
            r'By:.*?(\w+)</a>', webpage, 'uploader', fatal=False)

        return {
            'id': video_id,
            'url': video_url,
            'ext': 'mp4',
            'title': video_title,
            'description': video_description,
            'uploader': video_uploader
        }
