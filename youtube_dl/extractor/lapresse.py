from __future__ import unicode_literals

import re

from .common import InfoExtractor
from .limelight import LimelightMediaIE


class LaPresseIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?lapresse\.ca/videos/(.*)/(?P<id>[a-z0-9]{32})'
    _TEST = {
        'url': 'http://www.lapresse.ca/videos/actualites/201610/26/46-1-louisville-ou-la-vie-en-noir-et-blanc.php/c28cee30286f4c53ba4f62459dca4a7b',
        'info_dict': {
            'id': 'c28cee30286f4c53ba4f62459dca4a7b',
            'ext': 'mp4',
            'title': 'Louisville ou la vie en noir et blanc'
        }
    }

    def _real_extract(self, url):
        id = self._match_id(url)

        return self.url_result('limelight:media:%s' % id, ie=LimelightMediaIE.ie_key(), video_id=id)