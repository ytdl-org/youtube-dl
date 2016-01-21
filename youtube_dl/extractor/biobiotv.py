# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor


class BioBioTVIE(InfoExtractor):
    _VALID_URL = r'https?://tv\.biobiochile\.cl/notas/(?P<year>\d{4})/\d{2}/\d{2}/(?P<id>[\w-]+)(?:\.shtml)?'

    _TESTS = [{
        'url': 'http://tv.biobiochile.cl/notas/2015/10/21/sobre-camaras-y-camarillas-parlamentarias.shtml',
        'md5': '26f51f03cf580265defefb4518faec09',
        'info_dict': {
            'id': 'col_c266',
            'display_id': 'sobre-camaras-y-camarillas-parlamentarias',
            'ext': 'mp4',
            'title': 'Sobre Cámaras y camarillas parlamentarias - BioBioChile TV',
            'thumbnail': 'http://media.biobiochile.cl/wp-content/uploads/2015/10/atria-2010-730x350.jpg',
            'url': 'http://unlimited2-cl.digitalproserver.com/bbtv/2015/col_c266.mp4',
            'uploader': 'Fernando Atria',
        }
    }, {
        'url': 'http://tv.biobiochile.cl/notas/2015/10/22/ninos-transexuales-de-quien-es-la-decision.shtml',
        'md5': 'a8c868e6b5f6c17d56873d5633204f84',
        'info_dict': {
            'id': 'col_c270',
            'display_id': 'ninos-transexuales-de-quien-es-la-decision',
            'ext': 'mp4',
            'title': 'Niños transexuales: ¿De quién es la decisión? - BioBioChile TV',
            'thumbnail': 'http://media.biobiochile.cl/wp-content/uploads/2015/10/samantha-2210-730x350.jpg',
            'url': 'http://unlimited2-cl.digitalproserver.com/bbtv/2015/col_c270.mp4',
            'uploader': 'Samantha Morán',
        }
    }, {
        'url': 'http://tv.biobiochile.cl/notas/2015/10/21/exclusivo-hector-pinto-formador-de-chupete-revela-version-del-ex-delantero-albo.shtml',
        'md5': 'c8369b50d42ff0a4f6b969fbd1a7c32d',
        'info_dict': {
            'id': 'Keno_Pinto',
            'display_id': 'exclusivo-hector-pinto-formador-de-chupete-revela-version-del-ex-delantero-albo',
            'ext': 'mp4',
            'title': 'Exclusivo: Héctor Pinto, formador de “Chupete”, revela versión del ex delantero albo - BioBioChile TV',
            'thumbnail': 'http://media.biobiochile.cl/wp-content/uploads/2015/10/pinto-730x350.jpg',
            'url': 'http://unlimited2-cl.digitalproserver.com/bbtv/2015/Keno_Pinto.mp4',
            'uploader': 'Juan Pablo Echenique',
        }
    }]

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        display_id = mobj.group('id')
        year = mobj.group('year')

        webpage = self._download_webpage(url, display_id)

        title = self._og_search_title(webpage)

        thumbnail = self._og_search_thumbnail(webpage)

        video_id = self._html_search_regex(
            r'loadFWPlayerVideo\(\"player_0\", \"\d{4}/(.+)\.mp4\"\)', webpage, 'title')

        url = 'http://unlimited2-cl.digitalproserver.com/bbtv/' + year + '/' + video_id + '.mp4'

        return {
            'id': video_id,
            'title': title,
            'url': url,
            'display_id': display_id,
            'thumbnail': thumbnail,
            'uploader': self._search_regex(r'biobiochile\.cl/author[^"]+"[^>]*>([^<]+)<', webpage, 'uploader', fatal=False),
        }
