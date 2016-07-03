# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor


class FlipagramIE(InfoExtractor):
    _VALID_URL = r'https?:\/\/(?:www\.)?flipagram\.com\/f\/(?P<id>.+)'
    _TEST = {
        'url': 'https://flipagram.com/f/myrWjW9RJw',
        'md5': '541988fb6c4c7c375215ea22a4a21841',
        'info_dict': {
            'id': 'myrWjW9RJw',
            'ext': 'mp4',
            'title': 'Flipagram by crystaldolce featuring King and Lionheart by Of Monsters and Men',
            'width': 720,
            'height': 1280,
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        title = self._html_search_regex(r'<title>(.*)</title>', webpage, 'title')
        video_url = self._html_search_regex(r'"contentUrl":"(https?://[^\"]+)', webpage, 'video URL')
        width = self._html_search_regex(r'embed","width":([0-9]+)', webpage, 'width', fatal=False)
        height = self._html_search_regex(r'embed",.*"height":([0-9]+)', webpage, 'height', fatal=False)
        return {
            'id': video_id,
            'title': title,
            'url': video_url,
            'width': int(width),
            'height': int(height),
        }
