# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import (
    int_or_none,
    remove_end,
)


class GameStarIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?gamestar\.de/videos/.*,(?P<id>[0-9]+)\.html'
    _TEST = {
        'url': 'http://www.gamestar.de/videos/trailer,3/hobbit-3-die-schlacht-der-fuenf-heere,76110.html',
        'md5': '96974ecbb7fd8d0d20fca5a00810cea7',
        'info_dict': {
            'id': '76110',
            'ext': 'mp4',
            'title': 'Hobbit 3: Die Schlacht der Fünf Heere - Teaser-Trailer zum dritten Teil',
            'description': 'Der Teaser-Trailer zu Hobbit 3: Die Schlacht der Fünf Heere zeigt einige Szenen aus dem dritten Teil der Saga und kündigt den...',
            'thumbnail': 're:^https?://.*\.jpg$',
            'timestamp': 1406542020,
            'upload_date': '20140728',
            'duration': 17
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        url = 'http://gamestar.de/_misc/videos/portal/getVideoUrl.cfm?premium=0&videoId=' + video_id

        # TODO: there are multiple ld+json objects in the webpage,
        # while _search_json_ld finds only the first one
        json_ld = self._parse_json(self._search_regex(
            r'(?s)<script[^>]+type=(["\'])application/ld\+json\1[^>]*>(?P<json_ld>[^<]+VideoObject[^<]+)</script>',
            webpage, 'JSON-LD', group='json_ld'), video_id)
        info_dict = self._json_ld(json_ld, video_id)
        info_dict['title'] = remove_end(info_dict['title'], ' - GameStar')

        view_count = json_ld.get('interactionCount')
        comment_count = int_or_none(self._html_search_regex(
            r'([0-9]+) Kommentare</span>', webpage, 'comment_count',
            fatal=False))

        info_dict.update({
            'id': video_id,
            'url': url,
            'ext': 'mp4',
            'view_count': view_count,
            'comment_count': comment_count
        })

        return info_dict
