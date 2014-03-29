# encoding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor


class KickStarterIE(InfoExtractor):
    _VALID_URL = r'https?://www\.kickstarter\.com/projects/(?P<id>[^/]*)/.*'
    _TEST = {
        'url': 'https://www.kickstarter.com/projects/1404461844/intersection-the-story-of-josh-grant?ref=home_location',
        'md5': 'c81addca81327ffa66c642b5d8b08cab',
        'info_dict': {
            'id': '1404461844',
            'ext': 'mp4',
            'title': 'Intersection: The Story of Josh Grant by Kyle Cowling',
            'description': 'A unique motocross documentary that examines the '
                'life and mind of one of sports most elite athletes: Josh Grant.',
        },
    }

    def _real_extract(self, url):
        m = re.match(self._VALID_URL, url)
        video_id = m.group('id')
        webpage = self._download_webpage(url, video_id)

        video_url = self._search_regex(r'data-video-url="(.*?)"',
            webpage, 'video URL')
        video_title = self._html_search_regex(r'<title>(.*?)</title>',
            webpage, 'title').rpartition('— Kickstarter')[0].strip()

        return {
            'id': video_id,
            'url': video_url,
            'title': video_title,
            'description': self._og_search_description(webpage),
            'thumbnail': self._og_search_thumbnail(webpage),
        }
