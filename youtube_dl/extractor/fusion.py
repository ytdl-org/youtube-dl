from __future__ import unicode_literals

from .common import InfoExtractor
from .ooyala import OoyalaIE


class FusionIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?fusion\.net/video/(?P<id>\d+)'
    _TESTS = [{
        'url': 'http://fusion.net/video/201781/u-s-and-panamanian-forces-work-together-to-stop-a-vessel-smuggling-drugs/',
        'info_dict': {
            'id': 'ZpcWNoMTE6x6uVIIWYpHh0qQDjxBuq5P',
            'ext': 'mp4',
            'title': 'U.S. and Panamanian forces work together to stop a vessel smuggling drugs',
            'description': 'md5:0cc84a9943c064c0f46b128b41b1b0d7',
            'duration': 140.0,
        },
        'params': {
            'skip_download': True,
        },
        'add_ie': ['Ooyala'],
    }, {
        'url': 'http://fusion.net/video/201781',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        display_id = self._match_id(url)
        webpage = self._download_webpage(url, display_id)

        ooyala_code = self._search_regex(
            r'data-ooyala-id=(["\'])(?P<code>(?:(?!\1).)+)\1',
            webpage, 'ooyala code', group='code')

        return OoyalaIE._build_url_result(ooyala_code)
