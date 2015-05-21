from __future__ import unicode_literals

import json

from .common import InfoExtractor
from ..compat import (
    compat_urllib_parse,
    compat_urlparse,
)
from ..utils import (
    get_element_by_attribute,
    parse_duration,
    strip_jsonp,
)


class MiTeleIE(InfoExtractor):
    IE_NAME = 'mitele.es'
    _VALID_URL = r'http://www\.mitele\.es/[^/]+/[^/]+/[^/]+/(?P<id>[^/]+)/'

    _TESTS = [{
        'url': 'http://www.mitele.es/programas-tv/diario-de/la-redaccion/programa-144/',
        'info_dict': {
            'id': '0fce117d',
            'ext': 'mp4',
            'title': 'Programa 144 - Tor, la web invisible',
            'description': 'md5:3b6fce7eaa41b2d97358726378d9369f',
            'display_id': 'programa-144',
            'duration': 2913,
        },
        'params': {
            # m3u8 download
            'skip_download': True,
        },
    }]

    def _real_extract(self, url):
        episode = self._match_id(url)
        webpage = self._download_webpage(url, episode)
        embed_data_json = self._search_regex(
            r'(?s)MSV\.embedData\[.*?\]\s*=\s*({.*?});', webpage, 'embed data',
        ).replace('\'', '"')
        embed_data = json.loads(embed_data_json)

        domain = embed_data['mediaUrl']
        if not domain.startswith('http'):
            # only happens in telecinco.es videos
            domain = 'http://' + domain
        info_url = compat_urlparse.urljoin(
            domain,
            compat_urllib_parse.unquote(embed_data['flashvars']['host'])
        )
        info_el = self._download_xml(info_url, episode).find('./video/info')

        video_link = info_el.find('videoUrl/link').text
        token_query = compat_urllib_parse.urlencode({'id': video_link})
        token_info = self._download_json(
            embed_data['flashvars']['ov_tk'] + '?' + token_query,
            episode,
            transform_source=strip_jsonp
        )
        formats = self._extract_m3u8_formats(
            token_info['tokenizedUrl'], episode, ext='mp4')

        return {
            'id': embed_data['videoId'],
            'display_id': episode,
            'title': info_el.find('title').text,
            'formats': formats,
            'description': get_element_by_attribute('class', 'text', webpage),
            'thumbnail': info_el.find('thumb').text,
            'duration': parse_duration(info_el.find('duration').text),
        }
