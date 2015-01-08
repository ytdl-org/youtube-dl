from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import (
    parse_iso8601,
    int_or_none,
)


class DiscoveryIE(InfoExtractor):
    _VALID_URL = r'http://www\.discovery\.com\/[a-zA-Z0-9\-]*/[a-zA-Z0-9\-]*/videos/(?P<id>[a-zA-Z0-9_\-]*)(?:\.htm)?'
    _TEST = {
        'url': 'http://www.discovery.com/tv-shows/mythbusters/videos/mission-impossible-outtakes.htm',
        'md5': '3c69d77d9b0d82bfd5e5932a60f26504',
        'info_dict': {
            'id': 'mission-impossible-outtakes',
            'ext': 'flv',
            'title': 'Mission Impossible Outtakes',
            'description': ('Watch Jamie Hyneman and Adam Savage practice being'
                            ' each other -- to the point of confusing Jamie\'s dog -- and '
                            'don\'t miss Adam moon-walking as Jamie ... behind Jamie\'s'
                            ' back.'),
            'duration': 156,
            'timestamp': 1303099200,
            'upload_date': '20110418',
        },
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        info = self._parse_json(self._search_regex(
            r'(?s)<script type="application/ld\+json">(.*?)</script>',
            webpage, 'video info'), video_id)

        return {
            'id': video_id,
            'title': info['name'],
            'url': info['contentURL'],
            'description': info.get('description'),
            'thumbnail': info.get('thumbnailUrl'),
            'timestamp': parse_iso8601(info.get('uploadDate')),
            'duration': int_or_none(info.get('duration')),
        }
