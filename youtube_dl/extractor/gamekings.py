# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import (
    xpath_text,
    xpath_with_ns,
)
from .youtube import YoutubeIE


class GamekingsIE(InfoExtractor):
    _VALID_URL = r'https?://www\.gamekings\.nl/(?:videos|nieuws)/(?P<id>[^/]+)'
    _TESTS = [{
        # YouTube embed video
        'url': 'http://www.gamekings.nl/videos/phoenix-wright-ace-attorney-dual-destinies-review/',
        'md5': '5208d3a17adeaef829a7861887cb9029',
        'info_dict': {
            'id': 'HkSQKetlGOU',
            'ext': 'mp4',
            'title': 'Phoenix Wright: Ace Attorney - Dual Destinies Review',
            'description': 'md5:db88c0e7f47e9ea50df3271b9dc72e1d',
            'thumbnail': 're:^https?://.*\.jpg$',
            'uploader_id': 'UCJugRGo4STYMeFr5RoOShtQ',
            'uploader': 'Gamekings Vault',
            'upload_date': '20151123',
        },
        'add_ie': ['Youtube'],
    }, {
        # vimeo video
        'url': 'http://www.gamekings.nl/videos/the-legend-of-zelda-majoras-mask/',
        'md5': '12bf04dfd238e70058046937657ea68d',
        'info_dict': {
            'id': 'the-legend-of-zelda-majoras-mask',
            'ext': 'mp4',
            'title': 'The Legend of Zelda: Majora’s Mask',
            'description': 'md5:9917825fe0e9f4057601fe1e38860de3',
            'thumbnail': 're:^https?://.*\.jpg$',
        },
    }, {
        'url': 'http://www.gamekings.nl/nieuws/gamekings-extra-shelly-en-david-bereiden-zich-voor-op-de-livestream/',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)

        webpage = self._download_webpage(url, video_id)

        playlist_id = self._search_regex(
            r'gogoVideo\([^,]+,\s*"([^"]+)', webpage, 'playlist id')

        # Check if a YouTube embed is used
        if YoutubeIE.suitable(playlist_id):
            return self.url_result(playlist_id, ie='Youtube')

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
