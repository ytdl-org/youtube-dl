# coding: utf-8
from __future__ import unicode_literals

import base64
import io
import re
import sys

from .common import InfoExtractor
from ..compat import (
    compat_b64decode,
    compat_struct_unpack,
)
from ..utils import (
    clean_html,
    determine_ext,
    ExtractorError,
    float_or_none,
    qualities,
    std_headers,
)

_bytes_to_chr = (lambda x: x) if sys.version_info[0] == 2 else (lambda x: map(chr, x))


class RTVEPlayIE(InfoExtractor):
    IE_NAME = 'rtve.es:play'
    IE_DESC = 'RTVE Play'
    _VALID_URL = r'https?://(?:www\.)?rtve\.es/(?P<kind>(?:playz?|(?:m/)?alacarta)/(?:audios|videos)|filmoteca)/[^/]+/[^/]+/(?P<id>\d+)'

    _TESTS = [{
        'url': 'http://www.rtve.es/alacarta/videos/balonmano/o-swiss-cup-masculina-final-espana-suecia/2491869/',
        'md5': '2c70aacf8a415d1b4e7fcc0525951162',
        'info_dict': {
            'id': '2491869',
            'ext': 'mp4',
            'title': 'Final de la Swiss Cup masculina: España-Suecia',
            'description': 'Swiss Cup masculina, Final: España-Suecia.',
            'duration': 5024.566,
            'series': 'Balonmano',
        },
        'expected_warnings': ['Failed to download MPD manifest', 'Failed to download m3u8 information'],
    }, {
        'note': 'Live stream',
        'url': 'http://www.rtve.es/alacarta/videos/television/24h-live/1694255/',
        'info_dict': {
            'id': '1694255',
            'ext': 'mp4',
            'title': 're:^24H LIVE [0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}$',
            'description': '24H LIVE',
            'is_live': True,
        },
        'params': {
            'skip_download': 'live stream',
        },
    }, {
        'url': 'http://www.rtve.es/alacarta/videos/servir-y-proteger/servir-proteger-capitulo-104/4236788/',
        'md5': '30b8827cba25f39d1af5a7c482cc8ac5',
        'info_dict': {
            'id': '4236788',
            'ext': 'mp4',
            'title': 'Capítulo 104',
            'description': 'md5:caae29ae04291875e611dd667fe84641',
            'duration': 3222.0,
        },
        'expected_warnings': ['Failed to download MPD manifest', 'Failed to download m3u8 information'],
    }, {
        'url': 'http://www.rtve.es/m/alacarta/videos/cuentame-como-paso/cuentame-como-paso-t16-ultimo-minuto-nuestra-vida-capitulo-276/2969138/?media=tve',
        'only_matching': True,
    }, {
        'url': 'http://www.rtve.es/filmoteca/no-do/not-1-introduccion-primer-noticiario-espanol/1465256/',
        'only_matching': True,
    }, {
        'url': 'http://www.rtve.es/alacarta/audios/a-hombros-de-gigantes/palabra-ingeniero-codigos-informaticos-27-04-21/5889192/',
        'md5': 'ae06d27bff945c4e87a50f89f6ce48ce',
        'info_dict': {
            'id': '5889192',
            'ext': 'mp3',
            'title': 'Códigos informáticos',
            'description': 'md5:72b0d7c1ca20fd327bdfff7ac0171afb',
            'thumbnail': r're:https?://.+/1598856591583.jpg',
            'duration': 349.440,
        },
    }]

    def _real_initialize(self):
        user_agent_b64 = base64.b64encode(std_headers['User-Agent'].encode('utf-8')).decode('utf-8')
        self._manager = self._download_json(
            'http://www.rtve.es/odin/loki/' + user_agent_b64,
            None, 'Fetching manager info')['manager']

    @staticmethod
    def _decrypt_url(png):
        encrypted_data = io.BytesIO(compat_b64decode(png)[8:])
        while True:
            length = compat_struct_unpack('!I', encrypted_data.read(4))[0]
            chunk_type = encrypted_data.read(4)
            if chunk_type == b'IEND':
                break
            data = encrypted_data.read(length)
            if chunk_type == b'tEXt':
                alphabet_data, text = data.replace(b'\0', b'').split(b'#')
                components = text.split(b'%%')
                if len(components) < 2:
                    components.insert(0, b'')
                quality, url_data = components

                alphabet = []
                e = 0
                d = 0
                for l in _bytes_to_chr(alphabet_data):
                    if d == 0:
                        alphabet.append(l)
                        d = e = (e + 1) % 4
                    else:
                        d -= 1
                url = ''
                f = 0
                e = 3
                b = 1
                for letter in _bytes_to_chr(url_data):
                    if f == 0:
                        l = int(letter) * 10
                        f = 1
                    else:
                        if e == 0:
                            l += int(letter)
                            url += alphabet[l]
                            e = (b + 3) % 4
                            f = 0
                            b += 1
                        else:
                            e -= 1

                yield quality.decode(), url
            encrypted_data.read(4)  # CRC

    def _extract_png_formats(self, video_id):
        png = self._download_webpage(
            'http://ztnr.rtve.es/ztnr/movil/thumbnail/%s/videos/%s.png' % (self._manager, video_id),
            video_id, 'Downloading url information', query={'q': 'v2'})
        q = qualities(['Media', 'Alta', 'HQ', 'HD_READY', 'HD_FULL'])
        formats = []
        for quality, video_url in self._decrypt_url(png):
            ext = determine_ext(video_url)
            if ext == 'm3u8':
                formats.extend(self._extract_m3u8_formats(
                    video_url, video_id, 'mp4', 'm3u8_native',
                    m3u8_id='hls', fatal=False))
            elif ext == 'mpd':
                formats.extend(self._extract_mpd_formats(
                    video_url, video_id, 'dash', fatal=False))
            else:
                formats.append({
                    'format_id': quality,
                    'quality': q(quality),
                    'url': video_url,
                })
        self._sort_formats(formats)
        return formats

    def _real_extract(self, url):
        groups = re.match(self._VALID_URL, url).groupdict()
        is_audio = groups.get('kind') == 'play/audios'
        return self._real_extract_from_id(groups['id'], is_audio)

    def _real_extract_from_id(self, video_id, is_audio=False):
        kind = 'audios' if is_audio else 'videos'
        info = self._download_json(
            'http://www.rtve.es/api/%s/%s.json' % (kind, video_id),
            video_id)['page']['items'][0]
        if (info.get('pubState') or {}).get('code') == 'DESPU':
            raise ExtractorError('The video is no longer available', expected=True)
        title = info['title'].strip()
        formats = self._extract_png_formats(video_id)

        subtitles = None
        sbt_file = info.get('sbtFile')
        if sbt_file:
            subtitles = self.extract_subtitles(video_id, sbt_file)

        is_live = info.get('consumption') == 'live'

        return {
            'id': video_id,
            'title': self._live_title(title) if is_live else title,
            'formats': formats,
            'url': info.get('htmlUrl'),
            'description': clean_html(info.get('description')),
            'thumbnail': info.get('thumbnail'),
            'subtitles': subtitles,
            'duration': float_or_none(info.get('duration'), 1000),
            'is_live': is_live,
            'series': (info.get('programInfo') or {}).get('title'),
        }

    def _get_subtitles(self, video_id, sub_file):
        subs = self._download_json(
            sub_file + '.json', video_id,
            'Downloading subtitles info')['page']['items']
        return dict(
            (s['lang'], [{'ext': 'vtt', 'url': s['src']}])
            for s in subs)


class RTVEInfantilIE(RTVEPlayIE):
    IE_NAME = 'rtve.es:infantil'
    IE_DESC = 'RTVE infantil'
    _VALID_URL = r'https?://(?:www\.)?rtve\.es/infantil/serie/[^/]+/video/[^/]+/(?P<id>[0-9]+)/'

    _TESTS = [{
        'url': 'https://www.rtve.es/infantil/serie/dino-ranch/video/pequeno-gran-ayudante/6693248/',
        'md5': '06d3f57eec593ad93fe9dcf079fbd940',
        'info_dict': {
            'id': '6693248',
            'ext': 'mp4',
            'title': 'Un pequeño gran ayudante',
            'description': 'md5:144ca351e31f9ee99a637ab9fc2787d5',
            'thumbnail': r're:https?://.+/1663318364501\.jpg',
            'duration': 691.44,
        },
        'expected_warnings': ['Failed to download MPD manifest', 'Failed to download m3u8 information'],
    }]


class RTVELiveIE(RTVEPlayIE):
    IE_NAME = 'rtve.es:live'
    IE_DESC = 'RTVE.es live streams'
    _VALID_URL = r'https?://(?:www\.)?rtve\.es/play/videos/directo/(?P<id>.+)'

    _TESTS = [{
        'url': 'https://www.rtve.es/play/videos/directo/la-1/',
        'info_dict': {
            'id': '1688877',
            'ext': 'mp4',
            'title': 're:^La 1 [0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}$',
            'description': 'La 1',
        },
        'params': {
            'skip_download': 'live stream',
        }
    }, {
        'url': 'https://www.rtve.es/play/videos/directo/canales-lineales/la-1/',
        'info_dict': {
            'id': '1688877',
            'ext': 'mp4',
            'title': 're:^La 1 [0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}$',
            'description': 'La 1',
        },
        'params': {
            'skip_download': 'live stream',
        }
    }, {
        'url': 'https://www.rtve.es/play/videos/directo/canales-lineales/capilla-ardiente-isabel-westminster/10886/',
        'info_dict': {
            'id': '1938028',
            'ext': 'mp4',
            'title': 're:^Mas24 - 1 [0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}$',
            'description': 'Mas24 - 1',
        },
        'params': {
            'skip_download': 'live stream',
        }
    }]

    def _real_extract(self, url):
        webpage = self._download_webpage(url, self._match_id(url))
        asset_id = self._search_regex(
            r'class=["\'].*?\bvideoPlayer\b.*?["\'][^>]+data-setup=[^>]+?(?:"|&quot;)idAsset(?:"|&quot;)\s*:\s*(?:"|&quot;)(\d+)(?:"|&quot;)',
            webpage, 'internal video ID')
        return self._real_extract_from_id(asset_id)


class RTVETelevisionIE(InfoExtractor):
    IE_NAME = 'rtve.es:television'
    # https://www.rtve.es/SECTION/YYYYMMDD/CONTENT_SLUG/CONTENT_ID.shtml
    _VALID_URL = r'https?://(?:www\.)?rtve\.es/[^/]+/\d{8}/[^/]+/(?P<id>\d+)\.shtml'

    _TESTS = [{
        'url': 'https://www.rtve.es/television/20220916/destacados-festival-san-sebastian-rtve-play/2395620.shtml',
        'info_dict': {
            'id': '6668919',
            'ext': 'mp4',
            'title': 'Las películas del Festival de San Sebastián en RTVE Play',
            'description': 'El\xa0Festival de San Sebastián vuelve a llenarse de artistas. Y en su honor,\xa0RTVE Play\xa0destacará cada viernes una\xa0película galardonada\xa0con la\xa0Concha de Oro\xa0en su catálogo.',
            'duration': 20.048,
        },
        'params': {
            'skip_download': True,
        },
    }, {
        'url': 'https://www.rtve.es/noticias/20220917/penelope-cruz-san-sebastian-premio-nacional/2402565.shtml',
        'info_dict': {
            'id': '6694087',
            'ext': 'mp4',
            'title': 'Penélope Cruz recoge el Premio Nacional de Cinematografía: "No dejen nunca de proteger nuestro cine"',
            'description': 'md5:eda9e6baa78dbbbcc7708c0cc8150a91',
            'duration': 388.2,
        },
        'params': {
            'skip_download': True,
        },
    }, {
        'url': 'https://www.rtve.es/deportes/20220917/motogp-bagnaia-pole-marquez-decimotercero-motorland-aragon/2402566.shtml',
        'info_dict': {
            'id': '6694142',
            'ext': 'mp4',
            'title': "Bagnaia logra su quinta 'pole' del año y Márquez partirá decimotercero",
            'description': 'md5:07e2ccb983a046cb42f896cce225f0a7',
            'duration': 153.44,
        },
        'params': {
            'skip_download': True,
        },
    }, {
        'url': 'https://www.rtve.es/playz/20220807/covaleda-fest-final/2394809.shtml',
        'info_dict': {
            'id': '6665408',
            'ext': 'mp4',
            'title': 'Covaleda Fest (Soria) - Día 3 con Marc Seguí y Paranoid 1966',
            'description': 'Festivales Playz viaja a Covaleda, Soria, para contarte todo lo que sucede en el Covaleda Fest. Entrevistas, challenges a los artistas, juegos... Khan, Adriana Jiménez y María García no dejarán pasar ni una. ¡No te lo pierdas!',
            'duration': 12009.92,
        },
        'params': {
            'skip_download': True,
        },
    }]

    def _real_extract(self, url):
        page_id = self._match_id(url)
        webpage = self._download_webpage(url, page_id)

        alacarta_url = self._search_regex(
            r'data-location="alacarta_videos"[^<]+url&quot;:&quot;(https?://www\.rtve\.es/play.+?)&',
            webpage, 'alacarta url', default=None)
        if alacarta_url is None:
            raise ExtractorError(
                'The webpage doesn\'t contain any video', expected=True)

        return self.url_result(alacarta_url, ie=RTVEPlayIE.ie_key())
