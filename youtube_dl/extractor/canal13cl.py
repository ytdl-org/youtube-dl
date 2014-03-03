# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor


class Canal13clIE(InfoExtractor):
    _VALID_URL = r'^http://(?:www\.)?13\.cl/(?:[^/?#]+/)*(?P<id>[^/?#]+)'
    _TEST = {
        'url': 'http://www.13.cl/t13/nacional/el-circulo-de-hierro-de-michelle-bachelet-en-su-regreso-a-la-moneda',
        'md5': '4cb1fa38adcad8fea88487a078831755',
        'info_dict': {
            'id': '1403022125',
            'display_id': 'el-circulo-de-hierro-de-michelle-bachelet-en-su-regreso-a-la-moneda',
            'ext': 'mp4',
            'title': 'El "círculo de hierro" de Michelle Bachelet en su regreso a La Moneda',
            'description': '(Foto: Agencia Uno) En nueve días más, Michelle Bachelet va a asumir por segunda vez como presidenta de la República. Entre aquellos que la acompañarán hay caras que se repiten y otras que se consolidan en su entorno de colaboradores más cercanos.',
        }
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        display_id = mobj.group('id')

        webpage = self._download_webpage(url, display_id)

        title = self._html_search_meta(
            'twitter:title', webpage, 'title', fatal=True)
        description = self._html_search_meta(
            'twitter:description', webpage, 'description')
        url = self._html_search_regex(
            r'articuloVideo = \"(.*?)\"', webpage, 'url')
        real_id = self._search_regex(
            r'[^0-9]([0-9]{7,})[^0-9]', url, 'id', default=display_id)
        thumbnail = self._html_search_regex(
            r'articuloImagen = \"(.*?)\"', webpage, 'thumbnail')

        return {
            'id': real_id,
            'display_id': display_id,
            'url': url,
            'title': title,
            'description': description,
            'ext': 'mp4',
            'thumbnail': thumbnail,
        }
