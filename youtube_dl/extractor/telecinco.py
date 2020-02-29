# coding: utf-8
from __future__ import unicode_literals

import json
import re

from .common import InfoExtractor
from .ooyala import OoyalaIE
from ..utils import (
    clean_html,
    determine_ext,
    int_or_none,
    str_or_none,
    urljoin,
)


class TelecincoIE(InfoExtractor):
    IE_DESC = 'telecinco.es, cuatro.com and mediaset.es'
    _VALID_URL = r'https?://(?:www\.)?(?:telecinco\.es|cuatro\.com|mediaset\.es)/(?:[^/]+/)+(?P<id>.+?)\.html'

    _TESTS = [{
        'url': 'http://www.telecinco.es/robinfood/temporada-01/t01xp14/Bacalao-cocochas-pil-pil_0_1876350223.html',
        'info_dict': {
            'id': '1876350223',
            'title': 'Bacalao con kokotxas al pil-pil',
            'description': 'md5:1382dacd32dd4592d478cbdca458e5bb',
        },
        'playlist': [{
            'md5': 'adb28c37238b675dad0f042292f209a7',
            'info_dict': {
                'id': 'JEA5ijCnF6p5W08A1rNKn7',
                'ext': 'mp4',
                'title': 'Con Martín Berasategui, hacer un bacalao al pil-pil es fácil y divertido',
                'duration': 662,
            },
        }]
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

    def _parse_content(self, content, url):
        video_id = content['dataMediaId']
        if content.get('dataCmsId') == 'ooyala':
            return self.url_result(
                'ooyala:%s' % video_id, OoyalaIE.ie_key(), video_id)
        config_url = urljoin(url, content['dataConfig'])
        config = self._download_json(
            config_url, video_id, 'Downloading config JSON')
        title = config['info']['title']

        def mmc_url(mmc_type):
            return re.sub(
                r'/(?:flash|html5)\.json', '/%s.json' % mmc_type,
                config['services']['mmc'])

        duration = None
        formats = []
        for mmc_type in ('flash', 'html5'):
            mmc = self._download_json(
                mmc_url(mmc_type), video_id,
                'Downloading %s mmc JSON' % mmc_type, fatal=False)
            if not mmc:
                continue
            if not duration:
                duration = int_or_none(mmc.get('duration'))
            for location in mmc['locations']:
                gat = self._proto_relative_url(location.get('gat'), 'http:')
                gcp = location.get('gcp')
                ogn = location.get('ogn')
                if None in (gat, gcp, ogn):
                    continue
                token_data = {
                    'gcp': gcp,
                    'ogn': ogn,
                    'sta': 0,
                }
                media = self._download_json(
                    gat, video_id, data=json.dumps(token_data).encode('utf-8'),
                    headers={
                        'Content-Type': 'application/json;charset=utf-8',
                        'Referer': url,
                    }, fatal=False) or {}
                stream = media.get('stream') or media.get('file')
                if not stream:
                    continue
                ext = determine_ext(stream)
                if ext == 'f4m':
                    formats.extend(self._extract_f4m_formats(
                        stream + '&hdcore=3.2.0&plugin=aasp-3.2.0.77.18',
                        video_id, f4m_id='hds', fatal=False))
                elif ext == 'm3u8':
                    formats.extend(self._extract_m3u8_formats(
                        stream, video_id, 'mp4', 'm3u8_native',
                        m3u8_id='hls', fatal=False))
        self._sort_formats(formats)

        return {
            'id': video_id,
            'title': title,
            'formats': formats,
            'thumbnail': content.get('dataPoster') or config.get('poster', {}).get('imageUrl'),
            'duration': duration,
        }

    def _real_extract(self, url):
        display_id = self._match_id(url)
        webpage = self._download_webpage(url, display_id)
        article = self._parse_json(self._search_regex(
            r'window\.\$REACTBASE_STATE\.article(?:_multisite)?\s*=\s*({.+})',
            webpage, 'article'), display_id)['article']
        title = article.get('title')
        description = clean_html(article.get('leadParagraph'))
        if article.get('editorialType') != 'VID':
            entries = []
            for p in article.get('body', []):
                content = p.get('content')
                if p.get('type') != 'video' or not content:
                    continue
                entries.append(self._parse_content(content, url))
            return self.playlist_result(
                entries, str_or_none(article.get('id')), title, description)
        content = article['opening']['content']
        info = self._parse_content(content, url)
        info.update({
            'description': description,
        })
        return info
