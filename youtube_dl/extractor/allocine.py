# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import re
import json

from .common import InfoExtractor
from ..compat import compat_str
from ..utils import (
    qualities,
    unescapeHTML,
    xpath_element,
)


class AllocineIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?allocine\.fr/(?P<typ>article|video|film)/(fichearticle_gen_carticle=|player_gen_cmedia=|fichefilm_gen_cfilm=|video-)(?P<id>[0-9]+)(?:\.html)?'

    _TESTS = [{
        'url': 'http://www.allocine.fr/article/fichearticle_gen_carticle=18635087.html',
        'md5': '0c9fcf59a841f65635fa300ac43d8269',
        'info_dict': {
            'id': '19546517',
            'ext': 'mp4',
            'title': 'Astérix - Le Domaine des Dieux Teaser VF',
            'description': 'md5:abcd09ce503c6560512c14ebfdb720d2',
            'thumbnail': 're:http://.*\.jpg',
        },
    }, {
        'url': 'http://www.allocine.fr/video/player_gen_cmedia=19540403&cfilm=222257.html',
        'md5': 'd0cdce5d2b9522ce279fdfec07ff16e0',
        'info_dict': {
            'id': '19540403',
            'ext': 'mp4',
            'title': 'Planes 2 Bande-annonce VF',
            'description': 'Regardez la bande annonce du film Planes 2 (Planes 2 Bande-annonce VF). Planes 2, un film de Roberts Gannaway',
            'thumbnail': 're:http://.*\.jpg',
        },
    }, {
        'url': 'http://www.allocine.fr/film/fichefilm_gen_cfilm=181290.html',
        'md5': '101250fb127ef9ca3d73186ff22a47ce',
        'info_dict': {
            'id': '19544709',
            'ext': 'mp4',
            'title': 'Dragons 2 - Bande annonce finale VF',
            'description': 'md5:601d15393ac40f249648ef000720e7e3',
            'thumbnail': 're:http://.*\.jpg',
        },
    }, {
        'url': 'http://www.allocine.fr/video/video-19550147/',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        typ = mobj.group('typ')
        display_id = mobj.group('id')

        webpage = self._download_webpage(url, display_id)

        if typ == 'film':
            video_id = self._search_regex(r'href="/video/player_gen_cmedia=([0-9]+).+"', webpage, 'video id')
        else:
            player = self._search_regex(r'data-player=\'([^\']+)\'>', webpage, 'data player', default=None)
            if player:
                player_data = json.loads(player)
                video_id = compat_str(player_data['refMedia'])
            else:
                model = self._search_regex(r'data-model="([^"]+)">', webpage, 'data model')
                model_data = self._parse_json(unescapeHTML(model), display_id)
                video_id = compat_str(model_data['id'])

        xml = self._download_xml('http://www.allocine.fr/ws/AcVisiondataV4.ashx?media=%s' % video_id, display_id)

        video = xpath_element(xml, './/AcVisionVideo').attrib
        quality = qualities(['ld', 'md', 'hd'])

        formats = []
        for k, v in video.items():
            if re.match(r'.+_path', k):
                format_id = k.split('_')[0]
                formats.append({
                    'format_id': format_id,
                    'quality': quality(format_id),
                    'url': v,
                })
        self._sort_formats(formats)

        return {
            'id': video_id,
            'title': video['videoTitle'],
            'thumbnail': self._og_search_thumbnail(webpage),
            'formats': formats,
            'description': self._og_search_description(webpage),
        }
