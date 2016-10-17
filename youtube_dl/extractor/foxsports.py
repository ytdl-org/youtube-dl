from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import smuggle_url


class FoxSportsIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?foxsports\.com/(?:[^/]+/)*(?P<id>[^/]+)'

    _TEST = {
        'url': 'http://www.foxsports.com/video?vid=432609859715',
        'info_dict': {
            'id': 'gA0bHB3Ladz3',
            'ext': 'flv',
            'title': 'Courtney Lee on going up 2-0 in series vs. Blazers',
            'description': 'Courtney Lee talks about Memphis being focused.',
        },
        'add_ie': ['ThePlatform'],
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)

        webpage = self._download_webpage(url, video_id)

        config = self._parse_json(
            self._search_regex(
                r"data-player-config='([^']+)'", webpage, 'data player config'),
            video_id)

        return self.url_result(smuggle_url(
            config['releaseURL'] + '&manifest=f4m', {'force_smil_url': True}))
