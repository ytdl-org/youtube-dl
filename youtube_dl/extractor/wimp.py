from __future__ import unicode_literals

import re

from .common import InfoExtractor


class WimpIE(InfoExtractor):
    _VALID_URL = r'(?:http://)?(?:www\.)?wimp\.com/([^/]+)/'
    _TEST = {
        'url': 'http://www.wimp.com/deerfence/',
        'file': 'deerfence.flv',
        'md5': '8b215e2e0168c6081a1cf84b2846a2b5',
        'info_dict': {
            "title": "Watch Till End: Herd of deer jump over a fence.",
            "description": "These deer look as fluid as running water when they jump over this fence as a herd. This video is one that needs to be watched until the very end for the true majesty to be witnessed, but once it comes, it's sure to take your breath away.",
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
