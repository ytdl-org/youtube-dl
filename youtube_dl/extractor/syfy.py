from __future__ import unicode_literals

from .common import InfoExtractor


class SyfyIE(InfoExtractor):
    _VALID_URL = r'https?://www\.syfy\.com/[^/]+/videos/(?:\d+-)?(?P<id>[A-Za-z0-9-]+)'

    _TESTS = [{
        'url': 'http://www.syfy.com/sharknado3/videos/sharknado-3-trailer',
        'info_dict': {
            'id': 'Sueh0V5Eh6L6',
            'ext': 'm3u8',
            'title': 'Sharknado 3: Trailer',
            'description': 'This time, the entire east coast isn\'t safe. Sharknado 3 premieres July 22 at 9/8c on Syfy.',
        },
        'add_ie': ['ThePlatform'],
        'skip': 'Blocked outside the US',
        'params': {
            # rtmp download
            'skip_download': True,
        }
    }]

    def _real_extract(self, url):
        display_id = self._match_id(url)
        webpage = self._download_webpage(url, display_id)
        releaseURL = self._parse_json(self._html_search_regex(
            r'"syfy_mpx"\s*:\s*({[^}]+?})',
            webpage, 'syfy_mpx'), display_id)['releaseURL']
        return self.url_result(releaseURL)
