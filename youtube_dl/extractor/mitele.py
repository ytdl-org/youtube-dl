from __future__ import unicode_literals

from .common import InfoExtractor
from ..compat import (
    compat_urllib_parse,
    compat_urlparse,
)
from ..utils import (
    encode_dict,
    get_element_by_attribute,
    int_or_none,
)


class MiTeleIE(InfoExtractor):
    IE_DESC = 'mitele.es'
    _VALID_URL = r'http://www\.mitele\.es/[^/]+/[^/]+/[^/]+/(?P<id>[^/]+)/'

    _TESTS = [{
        'url': 'http://www.mitele.es/programas-tv/diario-de/la-redaccion/programa-144/',
        'md5': '0ff1a13aebb35d9bc14081ff633dd324',
        'info_dict': {
            'id': '0NF1jJnxS1Wu3pHrmvFyw2',
            'display_id': 'programa-144',
            'ext': 'flv',
            'title': 'Tor, la web invisible',
            'description': 'md5:3b6fce7eaa41b2d97358726378d9369f',
            'thumbnail': 're:(?i)^https?://.*\.jpg$',
            'duration': 2913,
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
                '%s/?%s' % (gat, compat_urllib_parse.urlencode(encode_dict(token_data))),
                display_id, 'Downloading %s JSON' % location['loc'])
            file_ = media.get('file')
            if not file_:
                continue
            formats.extend(self._extract_f4m_formats(
                file_ + '&hdcore=3.2.0&plugin=aasp-3.2.0.77.18',
                display_id, f4m_id=loc))

        title = self._search_regex(
            r'class="Destacado-text"[^>]*>\s*<strong>([^<]+)</strong>', webpage, 'title')

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
            'thumbnail': thumbnail,
            'duration': duration,
            'formats': formats,
        }
