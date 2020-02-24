# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor


class HGTVShowIE(InfoExtractor):
    IE_NAME = 'hgtv:show'
    _VALID_URL = r'https?://(?:www\.)?hgtv\.(?:com|ca)/shows/[^/]+/(?P<id>[^/?#&]+)'
    _TESTS = [{
        # data-module="video"
        'url': 'https://www.hgtv.com/shows/fixer-upper/fixer-upper-full-episodes-videos',
        'info_dict': {
            'id': 'fixer-upper-full-episodes-videos',
            'title': 'Fixer Upper - Full Episodes',
        },
        'playlist_mincount': 14,
    }, {
        # data-deferred-module="video"
        'url': 'http://www.hgtv.com/shows/good-bones/episodes/an-old-victorian-house-gets-a-new-facelift',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        display_id = self._match_id(url)

        webpage = self._download_webpage(url, display_id)

        config = self._parse_json(
            self._search_regex(
                r'(?s)data-(?:deferred-)?module=["\']video["\'][^>]*>.*?<script[^>]+type=["\']text/x-config["\'][^>]*>(.+?)</script',
                webpage, 'video config'),
            display_id)['channels'][0]

        entries = [
            self.url_result(video['releaseUrl'])
            for video in config['videos'] if video.get('releaseUrl')]

        return self.playlist_result(
            entries, display_id, config.get('title'), config.get('description'))
