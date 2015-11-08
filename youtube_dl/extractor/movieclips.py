# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..compat import (
    compat_urllib_request,
)


class MovieClipsIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www.)?movieclips\.com/videos/(?P<id>[^/?#]+)'
    _TEST = {
        'url': 'http://www.movieclips.com/videos/warcraft-trailer-1-561180739597?autoPlay=true&playlistId=5',
        'info_dict': {
            'id': 'pKIGmG83AqD9',
            'display_id': 'warcraft-trailer-1-561180739597',
            'ext': 'mp4',
            'title': 'Warcraft Trailer 1',
            'description': 'Watch Trailer 1 from Warcraft (2016). Legendary’s WARCRAFT is a 3D epic adventure of world-colliding conflict based.',
            'thumbnail': 're:^https?://.*\.jpg$',
        },
        'add_ie': ['ThePlatform'],
    }

    def _real_extract(self, url):
        display_id = self._match_id(url)

        req = compat_urllib_request.Request(url)
        # it doesn't work if it thinks the browser it's too old
        req.add_header('User-Agent', 'Mozilla/5.0 (X11; Linux x86_64; rv:10.0) Gecko/20150101 Firefox/43.0 (Chrome)')
        webpage = self._download_webpage(req, display_id)
        theplatform_link = self._html_search_regex(r'src="(http://player.theplatform.com/p/.*?)"', webpage, 'theplatform link')
        title = self._html_search_regex(r'<title[^>]*>([^>]+)-\s*\d+\s*|\s*Movieclips.com</title>', webpage, 'title')
        description = self._html_search_meta('description', webpage)

        return {
            '_type': 'url_transparent',
            'url': theplatform_link,
            'title': title,
            'display_id': display_id,
            'description': description,
        }
