from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    url_basename,
)


class EngadgetIE(InfoExtractor):
    _VALID_URL = r'''(?x)https?://www.engadget.com/
        (?:video(?:/5min)?/(?P<id>\d+)|
            [\d/]+/.*?)
        '''

    _TEST = {
        'url': 'http://www.engadget.com/video/5min/518153925/',
        'md5': 'c6820d4828a5064447a4d9fc73f312c9',
        'info_dict': {
            'id': '518153925',
            'ext': 'mp4',
            'title': 'Samsung Galaxy Tab Pro 8.4 Review',
        },
        'add_ie': ['FiveMin'],
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)

        if video_id is not None:
            return self.url_result('5min:%s' % video_id)
        else:
            title = url_basename(url)
            webpage = self._download_webpage(url, title)
            ids = re.findall(r'<iframe[^>]+?playList=(\d+)', webpage)
            return {
                '_type': 'playlist',
                'title': title,
                'entries': [self.url_result('5min:%s' % vid) for vid in ids]
            }
