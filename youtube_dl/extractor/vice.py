from __future__ import unicode_literals

from .common import InfoExtractor
from .ooyala import OoyalaIE
from ..utils import ExtractorError


class ViceIE(InfoExtractor):
    _VALID_URL = r'https?://(?:.+?\.)?vice\.com/(?:[^/]+/)+(?P<id>.+)'

    _TESTS = [
        {
            'url': 'http://www.vice.com/Fringes/cowboy-capitalists-part-1',
            'info_dict': {
                'id': '43cW1mYzpia9IlestBjVpd23Yu3afAfp',
                'ext': 'mp4',
                'title': 'VICE_COWBOYCAPITALISTS_PART01_v1_VICE_WM_1080p.mov',
            },
            'params': {
                # Requires ffmpeg (m3u8 manifest)
                'skip_download': True,
            },
        }, {
            'url': 'https://news.vice.com/video/experimenting-on-animals-inside-the-monkey-lab',
            'only_matching': True,
        }
    ]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)
        try:
            embed_code = self._search_regex(
                r'embedCode=([^&\'"]+)', webpage,
                'ooyala embed code')
            ooyala_url = OoyalaIE._url_for_embed_code(embed_code)
        except ExtractorError:
            raise ExtractorError('The page doesn\'t contain a video', expected=True)
        return self.url_result(ooyala_url, ie='Ooyala')
