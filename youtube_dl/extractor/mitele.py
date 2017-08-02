# coding: utf-8
from __future__ import unicode_literals

import uuid

from .common import InfoExtractor
from .ooyala import OoyalaIE
from ..compat import (
    compat_str,
    compat_urllib_parse_urlencode,
    compat_urlparse,
)
from ..utils import (
    int_or_none,
    extract_attributes,
    determine_ext,
    smuggle_url,
    parse_duration,
)


class MiTeleBaseIE(InfoExtractor):
    def _get_player_info(self, url, webpage):
        player_data = extract_attributes(self._search_regex(
            r'(?s)(<ms-video-player.+?</ms-video-player>)',
            webpage, 'ms video player'))
        video_id = player_data['data-media-id']
        if player_data.get('data-cms-id') == 'ooyala':
            return self.url_result(
                'ooyala:%s' % video_id, ie=OoyalaIE.ie_key(), video_id=video_id)
        config_url = compat_urlparse.urljoin(url, player_data['data-config'])
        config = self._download_json(
            config_url, video_id, 'Downloading config JSON')
        mmc_url = config['services']['mmc']

        duration = None
        formats = []
        for m_url in (mmc_url, mmc_url.replace('/flash.json', '/html5.json')):
            mmc = self._download_json(
                m_url, video_id, 'Downloading mmc JSON')
            if not duration:
                duration = int_or_none(mmc.get('duration'))
            for location in mmc['locations']:
                gat = self._proto_relative_url(location.get('gat'), 'http:')
                bas = location.get('bas')
                loc = location.get('loc')
                ogn = location.get('ogn')
                if None in (gat, bas, loc, ogn):
                    continue
                token_data = {
                    'bas': bas,
                    'icd': loc,
                    'ogn': ogn,
                    'sta': '0',
                }
                media = self._download_json(
                    '%s/?%s' % (gat, compat_urllib_parse_urlencode(token_data)),
                    video_id, 'Downloading %s JSON' % location['loc'])
                file_ = media.get('file')
                if not file_:
                    continue
                ext = determine_ext(file_)
                if ext == 'f4m':
                    formats.extend(self._extract_f4m_formats(
                        file_ + '&hdcore=3.2.0&plugin=aasp-3.2.0.77.18',
                        video_id, f4m_id='hds', fatal=False))
                elif ext == 'm3u8':
                    formats.extend(self._extract_m3u8_formats(
                        file_, video_id, 'mp4', 'm3u8_native', m3u8_id='hls', fatal=False))
        self._sort_formats(formats)

        return {
            'id': video_id,
            'formats': formats,
            'thumbnail': player_data.get('data-poster') or config.get('poster', {}).get('imageUrl'),
            'duration': duration,
        }


class MiTeleIE(InfoExtractor):
    IE_DESC = 'mitele.es'
    _VALID_URL = r'https?://(?:www\.)?mitele\.es/(?:[^/]+/)+(?P<id>[^/]+)/player'

    _TESTS = [{
        'url': 'http://www.mitele.es/programas-tv/diario-de/57b0dfb9c715da65618b4afa/player',
        'info_dict': {
            'id': '57b0dfb9c715da65618b4afa',
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
            'id': '57b0de3dc915da14058b4876',
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
        webpage = self._download_webpage(url, video_id)

        gigya_url = self._search_regex(
            r'<gigya-api>[^>]*</gigya-api>[^>]*<script\s+src="([^"]*)">[^>]*</script>',
            webpage, 'gigya', default=None)
        gigya_sc = self._download_webpage(
            compat_urlparse.urljoin('http://www.mitele.es/', gigya_url),
            video_id, 'Downloading gigya script')

        # Get a appKey/uuid for getting the session key
        appKey = self._search_regex(
            r'constant\s*\(\s*["\']_appGridApplicationKey["\']\s*,\s*["\']([0-9a-f]+)',
            gigya_sc, 'appKey')

        session_json = self._download_json(
            'https://appgrid-api.cloud.accedo.tv/session',
            video_id, 'Downloading session keys', query={
                'appKey': appKey,
                'uuid': compat_str(uuid.uuid4()),
            })

        paths = self._download_json(
            'https://appgrid-api.cloud.accedo.tv/metadata/general_configuration,%20web_configuration',
            video_id, 'Downloading paths JSON',
            query={'sessionKey': compat_str(session_json['sessionKey'])})

        ooyala_s = paths['general_configuration']['api_configuration']['ooyala_search']
        source = self._download_json(
            'http://%s%s%s/docs/%s' % (
                ooyala_s['base_url'], ooyala_s['full_path'],
                ooyala_s['provider_id'], video_id),
            video_id, 'Downloading data JSON', query={
                'include_titles': 'Series,Season',
                'product_name': 'test',
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
