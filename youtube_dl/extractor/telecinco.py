# coding: utf-8
from __future__ import unicode_literals

import json

from .common import InfoExtractor
from ..compat import (
    compat_urllib_parse_unquote,
    compat_urllib_parse_urlencode,
    compat_urlparse,
)
from ..utils import (
    get_element_by_attribute,
    parse_duration,
    strip_jsonp,
)


class TelecincoIE(InfoExtractor):
    IE_DESC = 'telecinco.es, cuatro.com and mediaset.es'
    _VALID_URL = r'https?://www\.(?:telecinco\.es|cuatro\.com|mediaset\.es)/(?:[^/]+/)+(?P<id>.+?)\.html'

    _TESTS = [{
        'url': 'http://www.telecinco.es/robinfood/temporada-01/t01xp14/Bacalao-cocochas-pil-pil_0_1876350223.html',
        'md5': '5cbef3ad5ef17bf0d21570332d140729',
        'info_dict': {
            'id': 'MDSVID20141015_0058',
            'ext': 'mp4',
            'title': 'Con Martín Berasategui, hacer un bacalao al ...',
            'duration': 662,
        },
    }, {
        'url': 'http://www.cuatro.com/deportes/futbol/barcelona/Leo_Messi-Champions-Roma_2_2052780128.html',
        'md5': '0a5b9f3cc8b074f50a0578f823a12694',
        'info_dict': {
            'id': 'MDSVID20150916_0128',
            'ext': 'mp4',
            'title': '¿Quién es este ex futbolista con el que hablan ...',
            'duration': 79,
        },
    }, {
        'url': 'http://www.mediaset.es/12meses/campanas/doylacara/conlatratanohaytrato/Ayudame-dar-cara-trata-trato_2_1986630220.html',
        'md5': 'ad1bfaaba922dd4a295724b05b68f86a',
        'info_dict': {
            'id': 'MDSVID20150513_0220',
            'ext': 'mp4',
            'title': '#DOYLACARA. Con la trata no hay trato',
            'duration': 50,
        },
    }, {
        'url': 'http://www.telecinco.es/informativos/nacional/Pablo_Iglesias-Informativos_Telecinco-entrevista-Pedro_Piqueras_2_1945155182.html',
        'only_matching': True,
    }, {
        'url': 'http://www.telecinco.es/espanasinirmaslejos/Espana-gran-destino-turistico_2_1240605043.html',
        'only_matching': True,
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
            compat_urllib_parse_unquote(embed_data['flashvars']['host'])
        )
        info_el = self._download_xml(info_url, episode).find('./video/info')

        video_link = info_el.find('videoUrl/link').text
        token_query = compat_urllib_parse_urlencode({'id': video_link})
        token_info = self._download_json(
            embed_data['flashvars']['ov_tk'] + '?' + token_query,
            episode,
            transform_source=strip_jsonp
        )
        formats = self._extract_m3u8_formats(
            token_info['tokenizedUrl'], episode, ext='mp4', entry_protocol='m3u8_native')
        self._sort_formats(formats)

        return {
            'id': embed_data['videoId'],
            'display_id': episode,
            'title': info_el.find('title').text,
            'formats': formats,
            'description': get_element_by_attribute('class', 'text', webpage),
            'thumbnail': info_el.find('thumb').text,
            'duration': parse_duration(info_el.find('duration').text),
        }
