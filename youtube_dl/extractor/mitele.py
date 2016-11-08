# coding: utf-8
from __future__ import unicode_literals

import uuid

from .common import InfoExtractor
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
    _VALID_URL = r'https?://(?:www\.)?mitele\.es/programas-tv/(?:[^/]+/)(?P<id>[^/]+)/player'

    _TESTS = [{
        'url': 'http://www.mitele.es/programas-tv/diario-de/57b0dfb9c715da65618b4afa/player',
        'info_dict': {
            'id': '57b0dfb9c715da65618b4afa',
            'ext': 'mp4',
            'title': 'Tor, la web invisible',
            'description': 'md5:3b6fce7eaa41b2d97358726378d9369f',
            'series': 'Diario de',
            'season': 'La redacción',
            'episode': 'Programa 144',
            'thumbnail': 're:(?i)^https?://.*\.jpg$',
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
            'episode': 'Programa 226',
            'thumbnail': 're:(?i)^https?://.*\.jpg$',
            'duration': 7313,
        },
        'params': {
            'skip_download': True,
        },
        'add_ie': ['Ooyala'],
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        gigya_url = self._search_regex(r'<gigya-api>[^>]*</gigya-api>[^>]*<script\s*src="([^"]*)">[^>]*</script>', webpage, 'gigya', default=None)
        gigya_sc = self._download_webpage(compat_urlparse.urljoin(r'http://www.mitele.es/', gigya_url), video_id, 'Downloading gigya script')
        # Get a appKey/uuid for getting the session key
        appKey_var = self._search_regex(r'value\("appGridApplicationKey",([0-9a-f]+)\)', gigya_sc, 'appKey variable')
        appKey = self._search_regex(r'var %s="([0-9a-f]+)"' % appKey_var, gigya_sc, 'appKey')
        uid = compat_str(uuid.uuid4())
        session_url = 'https://appgrid-api.cloud.accedo.tv/session?appKey=%s&uuid=%s' % (appKey, uid)
        session_json = self._download_json(session_url, video_id, 'Downloading session keys')
        sessionKey = compat_str(session_json['sessionKey'])

        paths_url = 'https://appgrid-api.cloud.accedo.tv/metadata/general_configuration,%20web_configuration?sessionKey=' + sessionKey
        paths = self._download_json(paths_url, video_id, 'Downloading paths JSON')
        ooyala_s = paths['general_configuration']['api_configuration']['ooyala_search']
        data_p = (
            'http://' + ooyala_s['base_url'] + ooyala_s['full_path'] + ooyala_s['provider_id'] +
            '/docs/' + video_id + '?include_titles=Series,Season&product_name=test&format=full')
        data = self._download_json(data_p, video_id, 'Downloading data JSON')
        source = data['hits']['hits'][0]['_source']
        embedCode = source['offers'][0]['embed_codes'][0]

        titles = source['localizable_titles'][0]
        title = titles.get('title_medium') or titles['title_long']
        episode = titles['title_sort_name']
        description = titles['summary_long']
        titles_series = source['localizable_titles_series'][0]
        series = titles_series['title_long']
        titles_season = source['localizable_titles_season'][0]
        season = titles_season['title_medium']
        duration = parse_duration(source['videos'][0]['duration'])

        return {
            '_type': 'url_transparent',
            # for some reason only HLS is supported
            'url': smuggle_url('ooyala:' + embedCode, {'supportedformats': 'm3u8'}),
            'id': video_id,
            'title': title,
            'description': description,
            'series': series,
            'season': season,
            'episode': episode,
            'duration': duration,
            'thumbnail': source['images'][0]['url'],
        }
