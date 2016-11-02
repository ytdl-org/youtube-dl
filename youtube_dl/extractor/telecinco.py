# coding: utf-8
from __future__ import unicode_literals

from .mitele import MiTeleBaseIE


class TelecincoIE(MiTeleBaseIE):
    IE_DESC = 'telecinco.es, cuatro.com and mediaset.es'
    _VALID_URL = r'https?://(?:www\.)?(?:telecinco\.es|cuatro\.com|mediaset\.es)/(?:[^/]+/)+(?P<id>.+?)\.html'

    _TESTS = [{
        'url': 'http://www.telecinco.es/robinfood/temporada-01/t01xp14/Bacalao-cocochas-pil-pil_0_1876350223.html',
        'md5': '8d7b2d5f699ee2709d992a63d5cd1712',
        'info_dict': {
            'id': 'JEA5ijCnF6p5W08A1rNKn7',
            'ext': 'mp4',
            'title': 'Bacalao con kokotxas al pil-pil',
            'description': 'md5:1382dacd32dd4592d478cbdca458e5bb',
            'duration': 662,
        },
    }, {
        'url': 'http://www.cuatro.com/deportes/futbol/barcelona/Leo_Messi-Champions-Roma_2_2052780128.html',
        'md5': '284393e5387b3b947b77c613ef04749a',
        'info_dict': {
            'id': 'jn24Od1zGLG4XUZcnUnZB6',
            'ext': 'mp4',
            'title': '¿Quién es este ex futbolista con el que hablan Leo Messi y Luis Suárez?',
            'description': 'md5:a62ecb5f1934fc787107d7b9a2262805',
            'duration': 79,
        },
    }, {
        'url': 'http://www.mediaset.es/12meses/campanas/doylacara/conlatratanohaytrato/Ayudame-dar-cara-trata-trato_2_1986630220.html',
        'md5': '749afab6ea5a136a8806855166ae46a2',
        'info_dict': {
            'id': 'aywerkD2Sv1vGNqq9b85Q2',
            'ext': 'mp4',
            'title': '#DOYLACARA. Con la trata no hay trato',
            'description': 'md5:2771356ff7bfad9179c5f5cd954f1477',
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
        display_id = self._match_id(url)
        webpage = self._download_webpage(url, display_id)
        title = self._html_search_meta(
            ['og:title', 'twitter:title'], webpage, 'title')
        info = self._get_player_info(url, webpage)
        info.update({
            'display_id': display_id,
            'title': title,
            'description': self._html_search_meta(
                ['og:description', 'twitter:description'],
                webpage, 'title', fatal=False),
        })
        return info
