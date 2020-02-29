# coding: utf-8
from __future__ import unicode_literals

import json
import re

from .common import InfoExtractor


class TelecincoIE(InfoExtractor):
    IE_DESC = 'telecinco.es, cuatro.com and mediaset.es'
    _VALID_URL = r'https?://(?:www\.)?(?:telecinco\.es|cuatro\.com|mediaset\.es)/(?:[^/]+/)+(?P<id>.+?)\.html'

    _TESTS = [{
        'url': 'http://www.telecinco.es/robinfood/temporada-01/t01xp14/Bacalao-cocochas-pil-pil_0_1876350223.html',
        'info_dict': {
            'id': '1876350223',
            'title': 'Con Martín Berasategui, hacer un bacalao al pil-pil es fácil y divertido',
            'ext': 'm3u8'
        }
    }, {
        'url': 'http://www.cuatro.com/deportes/futbol/barcelona/Leo_Messi-Champions-Roma_2_2052780128.html',
        'md5': '9468140ebc300fbb8b9d65dc6e5c4b43',
        'info_dict': {
            'id': 'jn24Od1zGLG4XUZcnUnZB6',
            'ext': 'mp4',
            'title': '¿Quién es este ex futbolista con el que hablan Leo Messi y Luis Suárez?',
            'description': 'md5:a62ecb5f1934fc787107d7b9a2262805',
            'duration': 79,
        },
    }, {
        'url': 'http://www.mediaset.es/12meses/campanas/doylacara/conlatratanohaytrato/Ayudame-dar-cara-trata-trato_2_1986630220.html',
        'md5': 'ae2dc6b7b50b2392076a51c0f70e01f6',
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
    }, {
        # ooyala video
        'url': 'http://www.cuatro.com/chesterinlove/a-carta/chester-chester_in_love-chester_edu_2_2331030022.html',
        'only_matching': True,
    }]

    def _real_extract(self, url):

        p = '(?P<host>:?[http|https].*://[^:/ ]+).?(?P<port>[0-9]*).*'
        m = re.search(p, url)
        host = m.group('host')

        (url_title, _, video_id) = self._match_id(url).split('_')
        webpage = self._download_webpage(url, video_id)

        m = re.search(r'dataConfig":"(?P<path>.*?)"', webpage)
        path = m.group('path')
        final = self._download_json(host + path, video_id)
        title = final['info']['title']
        mmc = final['services']['mmc']
        if not mmc.startswith('http'):
            mmc = 'http:' + mmc
        res = self._download_json(mmc, video_id)
        sta = 0
        location = res['locations'][sta]
        gateurl = 'https:' + location['gat']
        gcp = location['gcp']
        ogn = location['ogn']
        payload = {'sta': sta, 'gcp': gcp, 'ogn': ogn}
        res = self._download_json(gateurl, video_id, data=str.encode(json.dumps(payload)), headers={'Content-Type': 'application/json'})
        duration = res.get('duration')
        m8u_url = res['stream'].split('/master.m3u8')[0] + '/index_0_av.m3u8?null=0'

        response = {
            'id': video_id,
            'url': m8u_url,
            'title': title,
            'duration': duration
        }

        return response
