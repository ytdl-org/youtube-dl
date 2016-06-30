from __future__ import unicode_literals

from .common import InfoExtractor
from .ooyala import OoyalaIE


class FusionIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?fusion\.net/video/\d+/(?P<id>[\w-]+)'
    _TEST = {
        'url': 'http://fusion.net/video/201781/u-s-and-panamanian-forces-work-together-to-stop-a-vessel-smuggling-drugs/',
        'md5': '55c3dd61d2b96dc17c4ab6711d02a39e',
        'info_dict': {
            'id': 'ZpcWNoMTE6x6uVIIWYpHh0qQDjxBuq5P',
            'ext': 'mp4',
            'title': 'U.S. and Panamanian forces work together to stop a vessel smuggling drugs',
            'description': 'md5:0cc84a9943c064c0f46b128b41b1b0d7',
            'duration': 140.0,
        },
        'add_ie': ['Ooyala'],
    }

    def _real_extract(self, url):
        display_id = self._match_id(url)
        webpage = self._download_webpage(url, display_id)

        ooyala_code = self._search_regex(r'data-video-id="([^"]{32})"',
            webpage, 'ooyala code')

        return OoyalaIE._build_url_result(ooyala_code)
