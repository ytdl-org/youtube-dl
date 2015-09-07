# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import js_to_json


class Tele13IE(InfoExtractor):
    _VALID_URL = r'^http://(?:www\.)?t13\.cl/videos(?:/[^/]+)+/(?P<id>[\w-]+)'
    _TESTS = [
        {
            'url': 'http://www.t13.cl/videos/actualidad/el-circulo-de-hierro-de-michelle-bachelet-en-su-regreso-a-la-moneda',
            'md5': '4cb1fa38adcad8fea88487a078831755',
            'info_dict': {
                'id': 'el-circulo-de-hierro-de-michelle-bachelet-en-su-regreso-a-la-moneda',
                'ext': 'mp4',
                'title': 'El círculo de hierro de Michelle Bachelet en su regreso a La Moneda',
            },
            'params': {
                # HTTP Error 404: Not Found
                'skip_download': True,
            },
        },
        {
            'url': 'http://www.t13.cl/videos/mundo/tendencias/video-captan-misteriosa-bola-fuego-cielos-bangkok',
            'md5': '65d1ae54812c96f4b345dd21d3bb1adc',
            'info_dict': {
                'id': 'rOoKv2OMpOw',
                'ext': 'mp4',
                'title': 'Shooting star seen on 7-Sep-2015',
                'description': 'md5:a1cd2e74f6ee6851552c9cf5851d6b06',
                'uploader': 'Porjai Jaturongkhakun',
                'upload_date': '20150906',
                'uploader_id': 'UCnLY_3ezwNcDSC_Wc6suZxw',
            },
            'add_ie': ['Youtube'],
        }
    ]

    def _real_extract(self, url):
        display_id = self._match_id(url)

        webpage = self._download_webpage(url, display_id)

        setup_js = self._parse_json(
            js_to_json(
                self._search_regex(
                    r"jwplayer\('player-vivo'\).setup\((\{.*?\})\)",
                    webpage,
                    'setup code',
                    flags=re.DOTALL
                ).replace('\n//', '')
            ),
            display_id
        )
        title = setup_js['title']
        thumbnail = setup_js.get('image') or setup_js['playlist'][0].get('image')
        description = self._html_search_meta(
            'description', webpage, 'description')

        formats = []
        for f in setup_js['playlist'][0]['sources']:
            format_url = f['file']
            if format_url != '':
                if '.m3u8' in format_url:
                    formats.extend(self._extract_m3u8_formats(format_url, display_id))
                else:
                    if 'youtube.com' in format_url:
                        return self.url_result(format_url, 'Youtube')
                    else:
                        formats.append({'url': format_url, 'format_id': f.get('label')})

        return {
            'id': display_id,
            'title': title,
            'description': description,
            'thumbnail': thumbnail,
            'formats': formats,
        }
