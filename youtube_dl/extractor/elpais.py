# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import strip_jsonp, unified_strdate


class ElPaisIE(InfoExtractor):
    _VALID_URL = r'https?://(?:[^.]+\.)?elpais\.com/.*/(?P<id>[^/#?]+)\.html(?:$|[?#])'
    IE_DESC = 'El País'

    _TESTS = [{
        'url': 'http://blogs.elpais.com/la-voz-de-inaki/2014/02/tiempo-nuevo-recetas-viejas.html',
        'md5': '98406f301f19562170ec071b83433d55',
        'info_dict': {
            'id': 'tiempo-nuevo-recetas-viejas',
            'ext': 'mp4',
            'title': 'Tiempo nuevo, recetas viejas',
            'description': 'De lunes a viernes, a partir de las ocho de la mañana, Iñaki Gabilondo nos cuenta su visión de la actualidad nacional e internacional.',
            'upload_date': '20140206',
        }
    }, {
        'url': 'http://elcomidista.elpais.com/elcomidista/2016/02/24/articulo/1456340311_668921.html#?id_externo_nwl=newsletter_diaria20160303t',
        'md5': '3bd5b09509f3519d7d9e763179b013de',
        'info_dict': {
            'id': '1456340311_668921',
            'ext': 'mp4',
            'title': 'Cómo hacer el mejor café con cafetera italiana',
            'description': 'Que sí, que las cápsulas son cómodas. Pero si le pides algo más a la vida, quizá deberías aprender a usar bien la cafetera italiana. No tienes más que ver este vídeo y seguir sus siete normas básicas.',
            'upload_date': '20160303',
        }
    }, {
        'url': 'http://elpais.com/elpais/2017/01/26/ciencia/1485456786_417876.html',
        'md5': '9c79923a118a067e1a45789e1e0b0f9c',
        'info_dict': {
            'id': '1485456786_417876',
            'ext': 'mp4',
            'title': 'Hallado un barco de la antigua Roma que naufragó en Baleares hace 1.800 años',
            'description': 'La nave portaba cientos de ánforas y se hundió cerca de la isla de Cabrera por razones desconocidas',
            'upload_date': '20170127',
        },
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        prefix = self._html_search_regex(
            r'var\s+url_cache\s*=\s*"([^"]+)";', webpage, 'URL prefix')
        id_multimedia = self._search_regex(
            r"id_multimedia\s*=\s*'([^']+)'", webpage, 'ID multimedia', default=None)
        if id_multimedia:
            url_info = self._download_json(
                'http://elpais.com/vdpep/1/?pepid=' + id_multimedia, video_id, transform_source=strip_jsonp)
            video_suffix = url_info['mp4']
        else:
            video_suffix = self._search_regex(
                r"(?:URLMediaFile|urlVideo_\d+)\s*=\s*url_cache\s*\+\s*'([^']+)'", webpage, 'video URL')
        video_url = prefix + video_suffix
        thumbnail_suffix = self._search_regex(
            r"(?:URLMediaStill|urlFotogramaFijo_\d+)\s*=\s*url_cache\s*\+\s*'([^']+)'",
            webpage, 'thumbnail URL', fatal=False)
        thumbnail = (
            None if thumbnail_suffix is None
            else prefix + thumbnail_suffix)
        title = self._html_search_regex(
            (r"tituloVideo\s*=\s*'([^']+)'", webpage, 'title',
             r'<h2 class="entry-header entry-title.*?>(.*?)</h2>'),
            webpage, 'title')
        upload_date = unified_strdate(self._search_regex(
            r'<p class="date-header date-int updated"\s+title="([^"]+)">',
            webpage, 'upload date', default=None) or self._html_search_meta(
            'datePublished', webpage, 'timestamp'))

        return {
            'id': video_id,
            'url': video_url,
            'title': title,
            'description': self._og_search_description(webpage),
            'thumbnail': thumbnail,
            'upload_date': upload_date,
        }
