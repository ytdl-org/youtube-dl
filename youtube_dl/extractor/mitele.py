# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..compat import (
    compat_urllib_parse_urlencode,
    compat_urlparse,
)
from ..utils import (
    get_element_by_attribute,
    int_or_none,
    remove_start,
    extract_attributes,
    determine_ext,
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


class MiTeleIE(MiTeleBaseIE):
    IE_DESC = 'mitele.es'
    _VALID_URL = r'https?://(?:www\.)?mitele\.es/(?:[^/]+/){3}(?P<id>[^/]+)/'

    _TESTS = [{
        'url': 'http://www.mitele.es/programas-tv/diario-de/la-redaccion/programa-144/',
        # MD5 is unstable
        'info_dict': {
            'id': '0NF1jJnxS1Wu3pHrmvFyw2',
            'display_id': 'programa-144',
            'ext': 'mp4',
            'title': 'Tor, la web invisible',
            'description': 'md5:3b6fce7eaa41b2d97358726378d9369f',
            'series': 'Diario de',
            'season': 'La redacción',
            'episode': 'Programa 144',
            'thumbnail': 're:(?i)^https?://.*\.jpg$',
            'duration': 2913,
        },
    }, {
        # no explicit title
        'url': 'http://www.mitele.es/programas-tv/cuarto-milenio/temporada-6/programa-226/',
        'info_dict': {
            'id': 'eLZSwoEd1S3pVyUm8lc6F',
            'display_id': 'programa-226',
            'ext': 'mp4',
            'title': 'Cuarto Milenio - Temporada 6 - Programa 226',
            'description': 'md5:50daf9fadefa4e62d9fc866d0c015701',
            'series': 'Cuarto Milenio',
            'season': 'Temporada 6',
            'episode': 'Programa 226',
            'thumbnail': 're:(?i)^https?://.*\.jpg$',
            'duration': 7312,
        },
        'params': {
            'skip_download': True,
        },
    }]

    def _real_extract(self, url):
        display_id = self._match_id(url)

        webpage = self._download_webpage(url, display_id)

        info = self._get_player_info(url, webpage)

        title = self._search_regex(
            r'class="Destacado-text"[^>]*>\s*<strong>([^<]+)</strong>',
            webpage, 'title', default=None)

        mobj = re.search(r'''(?sx)
                            class="Destacado-text"[^>]*>.*?<h1>\s*
                            <span>(?P<series>[^<]+)</span>\s*
                            <span>(?P<season>[^<]+)</span>\s*
                            <span>(?P<episode>[^<]+)</span>''', webpage)
        series, season, episode = mobj.groups() if mobj else [None] * 3

        if not title:
            if mobj:
                title = '%s - %s - %s' % (series, season, episode)
            else:
                title = remove_start(self._search_regex(
                    r'<title>([^<]+)</title>', webpage, 'title'), 'Ver online ')

        info.update({
            'display_id': display_id,
            'title': title,
            'description': get_element_by_attribute('class', 'text', webpage),
            'series': series,
            'season': season,
            'episode': episode,
        })
        return info
