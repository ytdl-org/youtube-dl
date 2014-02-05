from __future__ import unicode_literals

import re

from .common import InfoExtractor


class FirstpostIE(InfoExtractor):
    IE_NAME = 'Firstpost.com'
    _VALID_URL = r'http://(?:www\.)?firstpost\.com/[^/]+/.*-(?P<id>[0-9]+)\.html'

    _TEST = {
        'url': 'http://www.firstpost.com/india/india-to-launch-indigenous-aircraft-carrier-monday-1025403.html',
        'md5': 'ee9114957692f01fb1263ed87039112a',
        'info_dict': {
            'id': '1025403',
            'ext': 'mp4',
            'title': 'India to launch indigenous aircraft carrier INS Vikrant today',
            'description': 'Its flight deck is over twice the size of a football field, its power unit can light up the entire Kochi city and the cabling is enough to cover the distance between here to Delhi.',
        }
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')

        webpage = self._download_webpage(url, video_id)
        video_url = self._html_search_regex(
            r'<div.*?name="div_video".*?flashvars="([^"]+)">',
            webpage, 'video URL')

        return {
            'id': video_id,
            'url': video_url,
            'title': self._og_search_title(webpage),
            'description': self._og_search_description(webpage),
            'thumbnail': self._og_search_thumbnail(webpage),
        }
