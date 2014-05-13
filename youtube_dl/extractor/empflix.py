from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
)


class EmpflixIE(InfoExtractor):
    _VALID_URL = r'^https?://www\.empflix\.com/videos/.*?-(?P<id>[0-9]+)\.html'
    _TEST = {
        'url': 'http://www.empflix.com/videos/Amateur-Finger-Fuck-33051.html',
        'md5': '5e5cc160f38ca9857f318eb97146e13e',
        'info_dict': {
            'id': '33051',
            'ext': 'flv',
            'title': 'Amateur Finger Fuck',
            'age_limit': 18,
        }
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')

        webpage = self._download_webpage(url, video_id)
        age_limit = self._rta_search(webpage)

        video_title = self._html_search_regex(
            r'name="title" value="(?P<title>[^"]*)"', webpage, 'title')

        cfg_url = self._html_search_regex(
            r'flashvars\.config = escape\("([^"]+)"',
            webpage, 'flashvars.config')

        cfg_xml = self._download_xml(
            cfg_url, video_id, note='Downloading metadata')
        video_url = cfg_xml.find('videoLink').text

        return {
            'id': video_id,
            'url': video_url,
            'ext': 'flv',
            'title': video_title,
            'age_limit': age_limit,
        }
