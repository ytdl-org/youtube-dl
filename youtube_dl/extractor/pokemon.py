# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    extract_attributes,
    int_or_none,
)


class PokemonIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?pokemon\.com/[a-z]{2}(?:.*?play=(?P<id>[a-z0-9]{32})|/(?:[^/]+/)+(?P<display_id>[^/?#&]+))'
    _TESTS = [{
        'url': 'https://www.pokemon.com/us/pokemon-episodes/20_30-the-ol-raise-and-switch/',
        'md5': '2fe8eaec69768b25ef898cda9c43062e',
        'info_dict': {
            'id': 'afe22e30f01c41f49d4f1d9eab5cd9a4',
            'ext': 'mp4',
            'title': 'The Ol’ Raise and Switch!',
            'description': 'md5:7db77f7107f98ba88401d3adc80ff7af',
            'timestamp': 1511824728,
            'upload_date': '20171127',
        },
        'add_id': ['LimelightMedia'],
    }, {
        # no data-video-title
        'url': 'https://www.pokemon.com/us/pokemon-episodes/pokemon-movies/pokemon-the-rise-of-darkrai-2008',
        'info_dict': {
            'id': '99f3bae270bf4e5097274817239ce9c8',
            'ext': 'mp4',
            'title': 'Pokémon: The Rise of Darkrai',
            'description': 'md5:ea8fbbf942e1e497d54b19025dd57d9d',
            'timestamp': 1417778347,
            'upload_date': '20141205',
        },
        'add_id': ['LimelightMedia'],
        'params': {
            'skip_download': True,
        },
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
        title = video_data.get('data-video-title') or self._html_search_meta(
            'pkm-title', webpage, ' title', default=None) or self._search_regex(
            r'<h1[^>]+\bclass=["\']us-title[^>]+>([^<]+)', webpage, 'title')
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
