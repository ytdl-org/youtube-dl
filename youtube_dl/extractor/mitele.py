from __future__ import unicode_literals

import re
import json

from .common import InfoExtractor
from ..utils import (
    compat_urllib_parse,
    compat_urlparse,
    get_element_by_attribute,
    parse_duration,
    strip_jsonp,
)


class MiTeleIE(InfoExtractor):
    IE_NAME = 'mitele.es'
    _VALID_URL = r'http://www\.mitele\.es/[^/]+/[^/]+/[^/]+/(?P<episode>[^/]+)/'

    _TEST = {
        'url': 'http://www.mitele.es/programas-tv/diario-de/la-redaccion/programa-144/',
        'md5': '6a75fe9d0d3275bead0cb683c616fddb',
        'info_dict': {
            'id': '0fce117d',
            'ext': 'mp4',
            'title': 'Programa 144 - Tor, la web invisible',
            'description': 'md5:3b6fce7eaa41b2d97358726378d9369f',
            'display_id': 'programa-144',
            'duration': 2913,
        },
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        episode = mobj.group('episode')
        webpage = self._download_webpage(url, episode)
        embed_data_json = self._search_regex(
            r'MSV\.embedData\[.*?\]\s*=\s*({.*?});', webpage, 'embed data',
            flags=re.DOTALL
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

        return {
            'id': embed_data['videoId'],
            'display_id': episode,
            'title': info_el.find('title').text,
            'url': token_info['tokenizedUrl'],
            'description': get_element_by_attribute('class', 'text', webpage),
            'thumbnail': info_el.find('thumb').text,
            'duration': parse_duration(info_el.find('duration').text),
        }
