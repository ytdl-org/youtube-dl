from __future__ import unicode_literals

import re

from .brightcove import BrightcoveIE
from .common import InfoExtractor
from ..utils import (
    ExtractorError,
)


class NownessIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?nowness\.com/[^?#]*?/(?P<id>[0-9]+)/(?P<slug>[^/]+?)(?:$|[?#])'

    _TEST = {
        'url': 'http://www.nowness.com/day/2013/6/27/3131/candor--the-art-of-gesticulation',
        'file': '2520295746001.mp4',
        'md5': '0ece2f70a7bd252c7b00f3070182d418',
        'info_dict': {
            'description': 'Candor: The Art of Gesticulation',
            'uploader': 'Nowness',
            'title': 'Candor: The Art of Gesticulation',
        }
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('slug')

        webpage = self._download_webpage(url, video_id)
        player_url = self._search_regex(
            r'"([^"]+/content/issue-[0-9.]+.js)"', webpage, 'player URL')
        real_id = self._search_regex(
            r'\sdata-videoId="([0-9]+)"', webpage, 'internal video ID')

        player_code = self._download_webpage(
            player_url, video_id,
            note='Downloading player JavaScript',
            errnote='Player download failed')
        player_code = player_code.replace("'+d+'", real_id)

        bc_url = BrightcoveIE._extract_brightcove_url(player_code)
        if bc_url is None:
            raise ExtractorError('Could not find player definition')
        return {
            '_type': 'url',
            'url': bc_url,
            'ie_key': 'Brightcove',
        }
