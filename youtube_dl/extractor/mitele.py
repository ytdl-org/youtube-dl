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
)


class MiTeleIE(InfoExtractor):
    IE_DESC = 'mitele.es'
    _VALID_URL = r'https?://www\.mitele\.es/[^/]+/[^/]+/[^/]+/(?P<id>[^/]+)/'

    _TESTS = [{
        'url': 'http://www.mitele.es/programas-tv/diario-de/la-redaccion/programa-144/',
        # MD5 is unstable
        'info_dict': {
            'id': '0NF1jJnxS1Wu3pHrmvFyw2',
            'display_id': 'programa-144',
            'ext': 'flv',
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
            'ext': 'flv',
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

        config_url = self._search_regex(
            r'data-config\s*=\s*"([^"]+)"', webpage, 'data config url')
        config_url = compat_urlparse.urljoin(url, config_url)

        config = self._download_json(
            config_url, display_id, 'Downloading config JSON')

        mmc = self._download_json(
            config['services']['mmc'], display_id, 'Downloading mmc JSON')

        formats = []
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
                display_id, 'Downloading %s JSON' % location['loc'])
            file_ = media.get('file')
            if not file_:
                continue
            formats.extend(self._extract_f4m_formats(
                file_ + '&hdcore=3.2.0&plugin=aasp-3.2.0.77.18',
                display_id, f4m_id=loc))
        self._sort_formats(formats)

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

        video_id = self._search_regex(
            r'data-media-id\s*=\s*"([^"]+)"', webpage,
            'data media id', default=None) or display_id
        thumbnail = config.get('poster', {}).get('imageUrl')
        duration = int_or_none(mmc.get('duration'))

        return {
            'id': video_id,
            'display_id': display_id,
            'title': title,
            'description': get_element_by_attribute('class', 'text', webpage),
            'series': series,
            'season': season,
            'episode': episode,
            'thumbnail': thumbnail,
            'duration': duration,
            'formats': formats,
        }
