# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from .nexx import NexxIE


class Tele5IE(InfoExtractor):
    _VALID_URL = r'https://www\.tele5\.de/(?:mediathek/filme-online/videos\?vid=|tv/)(?P<display_id>[\w-]+)'

    _TESTS = [{
        'url': 'https://www.tele5.de/mediathek/filme-online/videos?vid=1550589',
        'info_dict': {
            'id': '1550589',
            'ext': 'mp4',
            'upload_date': '20180822',
            'timestamp': 1534927316,
            'title': 'SchleFaZ: Atomic Shark',
        }
    }, {
        'url': 'https://www.tele5.de/tv/dark-matter/videos',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        display_id = mobj.group('display_id')

        webpage = self._download_webpage(url, display_id)

        video_id = self._html_search_regex(
            r'id\s*=\s*["\']video-player["\']\s*data-id\s*=\s*["\']([0-9]+)["\']',
            webpage, 'video_id')

        return self.url_result(
            'https://api.nexx.cloud/v3/759/videos/byid/%s' % video_id,
            ie=NexxIE.ie_key(), video_id=video_id)
