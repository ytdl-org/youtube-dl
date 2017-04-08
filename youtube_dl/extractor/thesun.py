from __future__ import unicode_literals

from .common import InfoExtractor
from .ooyala import OoyalaIE


class TheSunIE(InfoExtractor):
    _VALID_URL = r'https://(?:www\.)?thesun\.co\.uk/\w+/(?P<id>\d+)/[\w-]'
    _TEST = {
        'url': 'https://www.thesun.co.uk/tvandshowbiz/2261604/orlando-bloom-and-katy-perry-post-adorable-instagram-video-together-celebrating-thanksgiving-after-split-rumours/',
        'md5': '5667123b24f25f43f4c4f381ef34c5c2',
        'info_dict': {
            'id': 'h4OXN0NzE6rv6ObkEifKcNA-gYUw4xFf',
            'ext': 'mp4',
            'title': 'Katy Perry and Orlando Bloom shut down split rumours with cute Thanksgiving video',
            'description': 'Still going strong',
            'duration': 31.28,
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)

        webpage = self._download_webpage(url, video_id)
        ooyala_id = self._search_regex(r'id\s*=\s*"thesun-ooyala-player-([^"]+)"', webpage, 'ooyala id')

        return OoyalaIE._build_url_result(ooyala_id)
