from __future__ import unicode_literals

from .common import InfoExtractor

from ..compat import compat_urlparse
from ..utils import (
    int_or_none,
    qualities,
)


class TheSceneIE(InfoExtractor):
    _VALID_URL = r'https?://thescene\.com/watch/[^/]+/(?P<id>[^/#?]+)'

    _TEST = {
        'url': 'https://thescene.com/watch/vogue/narciso-rodriguez-spring-2013-ready-to-wear',
        'info_dict': {
            'id': '520e8faac2b4c00e3c6e5f43',
            'ext': 'mp4',
            'title': 'Narciso Rodriguez: Spring 2013 Ready-to-Wear',
            'display_id': 'narciso-rodriguez-spring-2013-ready-to-wear',
            'duration': 127,
            'series': 'Style.com Fashion Shows',
            'season': 'Ready To Wear Spring 2013',
            'tags': list,
            'categories': list,
        },
    }

    def _real_extract(self, url):
        display_id = self._match_id(url)

        webpage = self._download_webpage(url, display_id)

        player_url = compat_urlparse.urljoin(
            url,
            self._html_search_regex(
                r'id=\'js-player-script\'[^>]+src=\'(.+?)\'', webpage, 'player url'))

        player = self._download_webpage(player_url, display_id)
        info = self._parse_json(
            self._search_regex(
                r'(?m)video\s*:\s*({.+?}),$', player, 'info json'),
            display_id)

        video_id = info['id']
        title = info['title']

        qualities_order = qualities(('low', 'high'))
        formats = [{
            'format_id': '{0}-{1}'.format(f['type'].split('/')[0], f['quality']),
            'url': f['src'],
            'quality': qualities_order(f['quality']),
        } for f in info['sources']]
        self._sort_formats(formats)

        return {
            'id': video_id,
            'display_id': display_id,
            'title': title,
            'formats': formats,
            'thumbnail': info.get('poster_frame'),
            'duration': int_or_none(info.get('duration')),
            'series': info.get('series_title'),
            'season': info.get('season_title'),
            'tags': info.get('tags'),
            'categories': info.get('categories'),
        }
