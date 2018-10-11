# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import (
    int_or_none,
    smuggle_url,
    parse_duration,
)


class MiTeleIE(InfoExtractor):
    IE_DESC = 'mitele.es'
    _VALID_URL = r'https?://(?:www\.)?mitele\.es/(?:[^/]+/)+(?P<id>[^/]+)/player'

    _TESTS = [{
        'url': 'http://www.mitele.es/programas-tv/diario-de/57b0dfb9c715da65618b4afa/player',
        'info_dict': {
            'id': 'FhYW1iNTE6J6H7NkQRIEzfne6t2quqPg',
            'ext': 'mp4',
            'title': 'Tor, la web invisible',
            'description': 'md5:3b6fce7eaa41b2d97358726378d9369f',
            'series': 'Diario de',
            'season': 'La redacción',
            'season_number': 14,
            'season_id': 'diario_de_t14_11981',
            'episode': 'Programa 144',
            'episode_number': 3,
            'thumbnail': r're:(?i)^https?://.*\.jpg$',
            'duration': 2913,
        },
        'add_ie': ['Ooyala'],
    }, {
        # no explicit title
        'url': 'http://www.mitele.es/programas-tv/cuarto-milenio/57b0de3dc915da14058b4876/player',
        'info_dict': {
            'id': 'oyNG1iNTE6TAPP-JmCjbwfwJqqMMX3Vq',
            'ext': 'mp4',
            'title': 'Cuarto Milenio Temporada 6 Programa 226',
            'description': 'md5:5ff132013f0cd968ffbf1f5f3538a65f',
            'series': 'Cuarto Milenio',
            'season': 'Temporada 6',
            'season_number': 6,
            'season_id': 'cuarto_milenio_t06_12715',
            'episode': 'Programa 226',
            'episode_number': 24,
            'thumbnail': r're:(?i)^https?://.*\.jpg$',
            'duration': 7313,
        },
        'params': {
            'skip_download': True,
        },
        'add_ie': ['Ooyala'],
    }, {
        'url': 'http://www.mitele.es/series-online/la-que-se-avecina/57aac5c1c915da951a8b45ed/player',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)

        paths = self._download_json(
            'https://www.mitele.es/amd/agp/web/metadata/general_configuration',
            video_id, 'Downloading paths JSON')

        ooyala_s = paths['general_configuration']['api_configuration']['ooyala_search']
        base_url = ooyala_s.get('base_url', 'cdn-search-mediaset.carbyne.ps.ooyala.com')
        full_path = ooyala_s.get('full_path', '/search/v1/full/providers/')
        source = self._download_json(
            '%s://%s%s%s/docs/%s' % (
                ooyala_s.get('protocol', 'https'), base_url, full_path,
                ooyala_s.get('provider_id', '104951'), video_id),
            video_id, 'Downloading data JSON', query={
                'include_titles': 'Series,Season',
                'product_name': ooyala_s.get('product_name', 'test'),
                'format': 'full',
            })['hits']['hits'][0]['_source']

        embedCode = source['offers'][0]['embed_codes'][0]
        titles = source['localizable_titles'][0]

        title = titles.get('title_medium') or titles['title_long']

        description = titles.get('summary_long') or titles.get('summary_medium')

        def get(key1, key2):
            value1 = source.get(key1)
            if not value1 or not isinstance(value1, list):
                return
            if not isinstance(value1[0], dict):
                return
            return value1[0].get(key2)

        series = get('localizable_titles_series', 'title_medium')

        season = get('localizable_titles_season', 'title_medium')
        season_number = int_or_none(source.get('season_number'))
        season_id = source.get('season_id')

        episode = titles.get('title_sort_name')
        episode_number = int_or_none(source.get('episode_number'))

        duration = parse_duration(get('videos', 'duration'))

        return {
            '_type': 'url_transparent',
            # for some reason only HLS is supported
            'url': smuggle_url('ooyala:' + embedCode, {'supportedformats': 'm3u8,dash'}),
            'id': video_id,
            'title': title,
            'description': description,
            'series': series,
            'season': season,
            'season_number': season_number,
            'season_id': season_id,
            'episode': episode,
            'episode_number': episode_number,
            'duration': duration,
            'thumbnail': get('images', 'url'),
        }
