# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import (
    xpath_text,
    xpath_with_ns,
)


class GamekingsIE(InfoExtractor):
    _VALID_URL = r'http://www\.gamekings\.tv/(?:videos|nieuws)/(?P<id>[^/]+)'
    _TESTS = [{
        'url': 'http://www.gamekings.tv/videos/phoenix-wright-ace-attorney-dual-destinies-review/',
        # MD5 is flaky, seems to change regularly
        # 'md5': '2f32b1f7b80fdc5cb616efb4f387f8a3',
        'info_dict': {
            'id': 'phoenix-wright-ace-attorney-dual-destinies-review',
            'ext': 'mp4',
            'title': 'Phoenix Wright: Ace Attorney \u2013 Dual Destinies Review',
            'description': 'md5:36fd701e57e8c15ac8682a2374c99731',
            'thumbnail': 're:^https?://.*\.jpg$',
        },
    }, {
        # vimeo video
        'url': 'http://www.gamekings.tv/videos/the-legend-of-zelda-majoras-mask/',
        'md5': '12bf04dfd238e70058046937657ea68d',
        'info_dict': {
            'id': 'the-legend-of-zelda-majoras-mask',
            'ext': 'mp4',
            'title': 'The Legend of Zelda: Majora’s Mask',
            'description': 'md5:9917825fe0e9f4057601fe1e38860de3',
            'thumbnail': 're:^https?://.*\.jpg$',
        },
    }, {
        'url': 'http://www.gamekings.tv/nieuws/gamekings-extra-shelly-en-david-bereiden-zich-voor-op-de-livestream/',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)

        webpage = self._download_webpage(url, video_id)

        playlist_id = self._search_regex(
            r'gogoVideo\(\s*\d+\s*,\s*"([^"]+)', webpage, 'playlist id')

        playlist = self._download_xml(
            'http://www.gamekings.tv/wp-content/themes/gk2010/rss_playlist.php?id=%s' % playlist_id,
            video_id)

        NS_MAP = {
            'jwplayer': 'http://rss.jwpcdn.com/'
        }

        item = playlist.find('./channel/item')

        thumbnail = xpath_text(item, xpath_with_ns('./jwplayer:image', NS_MAP), 'thumbnail')
        video_url = item.find(xpath_with_ns('./jwplayer:source', NS_MAP)).get('file')

        return {
            'id': video_id,
            'url': video_url,
            'title': self._og_search_title(webpage),
            'description': self._og_search_description(webpage),
            'thumbnail': thumbnail,
        }
