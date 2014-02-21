from __future__ import unicode_literals

import re

from .common import InfoExtractor


class WimpIE(InfoExtractor):
    _VALID_URL = r'http://(?:www\.)?wimp\.com/([^/]+)/'
    _TEST = {
        'url': 'http://www.wimp.com/maruexhausted/',
        'md5': 'f1acced123ecb28d9bb79f2479f2b6a1',
        'info_dict': {
            'id': 'maruexhausted',
            'ext': 'flv',
            'title': 'Maru is exhausted.',
            'description': 'md5:57e099e857c0a4ea312542b684a869b8',
        }
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group(1)
        webpage = self._download_webpage(url, video_id)
        video_url = self._search_regex(
            r's1\.addVariable\("file",\s*"([^"]+)"\);', webpage, 'video URL')

        return {
            'id': video_id,
            'url': video_url,
            'title': self._og_search_title(webpage),
            'thumbnail': self._og_search_thumbnail(webpage),
            'description': self._og_search_description(webpage),
        }