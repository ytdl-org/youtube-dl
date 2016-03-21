from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import ExtractorError


class FreeVideoIE(InfoExtractor):
    _VALID_URL = r'^https?://www.freevideo.cz/vase-videa/(?P<id>[^.]+)\.html(?:$|[?#])'

    _TEST = {
        'url': 'http://www.freevideo.cz/vase-videa/vysukany-zadecek-22033.html',
        'info_dict': {
            'id': 'vysukany-zadecek-22033',
            'ext': 'mp4',
            'title': 'vysukany-zadecek-22033',
            'age_limit': 18,
        },
        'skip': 'Blocked outside .cz',
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage, handle = self._download_webpage_handle(url, video_id)
        if '//www.czechav.com/' in handle.geturl():
            raise ExtractorError(
                'Access to freevideo is blocked from your location',
                expected=True)

        video_url = self._search_regex(
            r'\s+url: "(http://[a-z0-9-]+.cdn.freevideo.cz/stream/.*?/video.mp4)"',
            webpage, 'video URL')

        return {
            'id': video_id,
            'url': video_url,
            'title': video_id,
            'age_limit': 18,
        }
