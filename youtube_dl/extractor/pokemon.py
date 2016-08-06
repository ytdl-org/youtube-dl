# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    extract_attributes,
    int_or_none,
)


class PokemonIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?pokemon\.com/[a-z]{2}(?:.*?play=(?P<id>[a-z0-9]{32})|/[^/]+/\d+_\d+-(?P<display_id>[^/?#]+))'
    _TESTS = [{
        'url': 'http://www.pokemon.com/us/pokemon-episodes/19_01-from-a-to-z/?play=true',
        'md5': '9fb209ae3a569aac25de0f5afc4ee08f',
        'info_dict': {
            'id': 'd0436c00c3ce4071ac6cee8130ac54a1',
            'ext': 'mp4',
            'title': 'From A to Z!',
            'description': 'Bonnie makes a new friend, Ash runs into an old friend, and a terrifying premonition begins to unfold!',
            'timestamp': 1460478136,
            'upload_date': '20160412',
        },
        'add_id': ['LimelightMedia']
    }, {
        'url': 'http://www.pokemon.com/uk/pokemon-episodes/?play=2e8b5c761f1d4a9286165d7748c1ece2',
        'only_matching': True,
    }, {
        'url': 'http://www.pokemon.com/fr/episodes-pokemon/18_09-un-hiver-inattendu/',
        'only_matching': True,
    }, {
        'url': 'http://www.pokemon.com/de/pokemon-folgen/01_20-bye-bye-smettbo/',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        video_id, display_id = re.match(self._VALID_URL, url).groups()
        webpage = self._download_webpage(url, video_id or display_id)
        video_data = extract_attributes(self._search_regex(
            r'(<[^>]+data-video-id="%s"[^>]*>)' % (video_id if video_id else '[a-z0-9]{32}'),
            webpage, 'video data element'))
        video_id = video_data['data-video-id']
        title = video_data['data-video-title']
        return {
            '_type': 'url_transparent',
            'id': video_id,
            'url': 'limelight:media:%s' % video_id,
            'title': title,
            'description': video_data.get('data-video-summary'),
            'thumbnail': video_data.get('data-video-poster'),
            'series': 'Pokémon',
            'season_number': int_or_none(video_data.get('data-video-season')),
            'episode': title,
            'episode_number': int_or_none(video_data.get('data-video-episode')),
            'ie_key': 'LimelightMedia',
        }
