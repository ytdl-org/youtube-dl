# coding: utf-8
from __future__ import unicode_literals
from .common import InfoExtractor

class LcpIE(InfoExtractor):
    IE_NAME = 'LCP'
    _VALID_URL = r'https?://(?:www\.)?lcp\.fr/(?:[^\/]+/)*(?P<id>[^/]+)'

    _TESTS = [{
        'url': 'http://www.lcp.fr/la-politique-en-video/schwartzenberg-prg-preconise-francois-hollande-de-participer-une-primaire',
        'md5': 'ab96c4dae94322ece1e98d97c8dc7807',
        'info_dict': {
            'id': 'd56d03e9',
            'url': 're:http://httpod.scdn.arkena.com/11970/d56d03e9_.*',
            'ext': 'mp4',
            'title': 'd56d03e9',
            'upload_date': '20160226',
            'timestamp': 1456488895
        }
    }, {
        'url': 'http://www.lcp.fr/le-direct',
        'info_dict': {
            'title': 'Le direct | LCP Assembl\xe9e nationale',
            'id': 'le-direct',
        },
        'playlist_mincount': 1
    }]

    def _real_extract(self, url):
        display_id = self._match_id(url)
        webpage = self._download_webpage(url, display_id)

        embed_url_regex = r'"(?P<url>(?:https?://(?:www\.)?)?play\.lcp\.fr/embed/[A-za-z0-9]+/[A-za-z0-9]+/[A-za-z0-9]+/[A-za-z0-9]+)"'
        embed_url = self._html_search_regex(embed_url_regex, webpage, 'player_url', default=None, fatal=False)
        if not embed_url:
            return self.url_result(url, 'Generic')

        title = self._og_search_title(webpage, default=None)
        return self.url_result(embed_url, 'ArkenaPlay', video_id=display_id, video_title=title)
