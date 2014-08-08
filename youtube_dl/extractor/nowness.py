# encoding: utf-8
from __future__ import unicode_literals

import re

from .brightcove import BrightcoveIE
from .common import InfoExtractor
from ..utils import ExtractorError


class NownessIE(InfoExtractor):
    _VALID_URL = r'https?://(?:(?:www|cn)\.)?nowness\.com/[^?#]*?/(?P<id>[0-9]+)/(?P<slug>[^/]+?)(?:$|[?#])'

    _TESTS = [
        {
            'url': 'http://www.nowness.com/day/2013/6/27/3131/candor--the-art-of-gesticulation',
            'md5': '068bc0202558c2e391924cb8cc470676',
            'info_dict': {
                'id': '2520295746001',
                'ext': 'mp4',
                'title': 'Candor: The Art of Gesticulation',
                'description': 'Candor: The Art of Gesticulation',
                'thumbnail': 're:^https?://.*\.jpg',
                'uploader': 'Nowness',
            }
        },
        {
            'url': 'http://cn.nowness.com/day/2014/8/7/4069/kasper-bj-rke-ft-jaakko-eino-kalevi--tnr',
            'md5': 'e79cf125e387216f86b2e0a5b5c63aa3',
            'info_dict': {
                'id': '3716354522001',
                'ext': 'mp4',
                'title': 'Kasper Bjørke ft. Jaakko Eino Kalevi: TNR',
                'description': 'Kasper Bjørke ft. Jaakko Eino Kalevi: TNR',
                'thumbnail': 're:^https?://.*\.jpg',
                'uploader': 'Nowness',
            }
        },
    ]

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
