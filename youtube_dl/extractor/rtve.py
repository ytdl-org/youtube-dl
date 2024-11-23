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
    determine_ext,
    ExtractorError,
    float_or_none,
    qualities,
    remove_end,
    remove_start,
    std_headers,
)

_bytes_to_chr = (lambda x: x) if sys.version_info[0] == 2 else (lambda x: map(chr, x))


class RTVEALaCartaIE(InfoExtractor):
    IE_NAME = 'rtve.es:alacarta'
    IE_DESC = 'RTVE a la carta'
    _VALID_URL = r'https?://(?:www\.)?rtve\.es/(m/)?(alacarta/videos|filmoteca)/[^/]+/[^/]+/(?P<id>\d+)'

    _TESTS = [{
        'url': 'http://www.rtve.es/alacarta/videos/balonmano/o-swiss-cup-masculina-final-espana-suecia/2491869/',
        'md5': '1d49b7e1ca7a7502c56a4bf1b60f1b43',
        'info_dict': {
            'id': '2491869',
            'ext': 'mp4',
            'title': 'Balonmano - Swiss Cup masculina. Final: España-Suecia',
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
            'is_live': True,
        },
        'params': {
            'skip_download': 'live stream',
        },
    }, {
        'url': 'http://www.rtve.es/alacarta/videos/servir-y-proteger/servir-proteger-capitulo-104/4236788/',
        'md5': 'd850f3c8731ea53952ebab489cf81cbf',
        'info_dict': {
            'id': '4236788',
            'ext': 'mp4',
            'title': 'Servir y proteger - Capítulo 104',
            'duration': 3222.0,
        },
        'expected_warnings': ['Failed to download MPD manifest', 'Failed to download m3u8 information'],
    }, {
        'url': 'http://www.rtve.es/m/alacarta/videos/cuentame-como-paso/cuentame-como-paso-t16-ultimo-minuto-nuestra-vida-capitulo-276/2969138/?media=tve',
        'only_matching': True,
    }, {
        'url': 'http://www.rtve.es/filmoteca/no-do/not-1-introduccion-primer-noticiario-espanol/1465256/',
        'only_matching': True,
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
                alphabet_data, text = data.split(b'\0')
                quality, url_data = text.split(b'%%')
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
            'http://www.rtve.es/ztnr/movil/thumbnail/%s/videos/%s.png' % (self._manager, video_id),
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
        video_id = self._match_id(url)
        info = self._download_json(
            'http://www.rtve.es/api/videos/%s/config/alacarta_videos.json' % video_id,
            video_id)['page']['items'][0]
        if info['state'] == 'DESPU':
            raise ExtractorError('The video is no longer available', expected=True)
        title = info['title'].strip()
        formats = self._extract_png_formats(video_id)

        subtitles = None
        sbt_file = info.get('sbtFile')
        if sbt_file:
            subtitles = self.extract_subtitles(video_id, sbt_file)

        is_live = info.get('live') is True

        return {
            'id': video_id,
            'title': self._live_title(title) if is_live else title,
            'formats': formats,
            'thumbnail': info.get('image'),
            'subtitles': subtitles,
            'duration': float_or_none(info.get('duration'), 1000),
            'is_live': is_live,
            'series': info.get('programTitle'),
        }

    def _get_subtitles(self, video_id, sub_file):
        subs = self._download_json(
            sub_file + '.json', video_id,
            'Downloading subtitles info')['page']['items']
        return dict(
            (s['lang'], [{'ext': 'vtt', 'url': s['src']}])
            for s in subs)


class RTVEInfantilIE(RTVEALaCartaIE):
    IE_NAME = 'rtve.es:infantil'
    IE_DESC = 'RTVE infantil'
    _VALID_URL = r'https?://(?:www\.)?rtve\.es/infantil/serie/[^/]+/video/[^/]+/(?P<id>[0-9]+)/'

    _TESTS = [{
        'url': 'http://www.rtve.es/infantil/serie/cleo/video/maneras-vivir/3040283/',
        'md5': '5747454717aedf9f9fdf212d1bcfc48d',
        'info_dict': {
            'id': '3040283',
            'ext': 'mp4',
            'title': 'Maneras de vivir',
            'thumbnail': r're:https?://.+/1426182947956\.JPG',
            'duration': 357.958,
        },
        'expected_warnings': ['Failed to download MPD manifest', 'Failed to download m3u8 information'],
    }]


class RTVELiveIE(RTVEALaCartaIE):
    IE_NAME = 'rtve.es:live'
    IE_DESC = 'RTVE.es live streams'
    _VALID_URL = r'https?://(?:www\.)?rtve\.es/directo/(?P<id>[a-zA-Z0-9-]+)'

    _TESTS = [{
        'url': 'http://www.rtve.es/directo/la-1/',
        'info_dict': {
            'id': 'la-1',
            'ext': 'mp4',
            'title': 're:^La 1 [0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}$',
        },
        'params': {
            'skip_download': 'live stream',
        }
    }]

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')

        webpage = self._download_webpage(url, video_id)
        title = remove_end(self._og_search_title(webpage), ' en directo en RTVE.es')
        title = remove_start(title, 'Estoy viendo ')

        vidplayer_id = self._search_regex(
            (r'playerId=player([0-9]+)',
             r'class=["\'].*?\blive_mod\b.*?["\'][^>]+data-assetid=["\'](\d+)',
             r'data-id=["\'](\d+)'),
            webpage, 'internal video ID')

        return {
            'id': video_id,
            'title': self._live_title(title),
            'formats': self._extract_png_formats(vidplayer_id),
            'is_live': True,
        }


class RTVETelevisionIE(InfoExtractor):
    IE_NAME = 'rtve.es:television'
    _VALID_URL = r'https?://(?:www\.)?rtve\.es/television/[^/]+/[^/]+/(?P<id>\d+).shtml'

    _TEST = {
        'url': 'http://www.rtve.es/television/20160628/revolucion-del-movil/1364141.shtml',
        'info_dict': {
            'id': '3069778',
            'ext': 'mp4',
            'title': 'Documentos TV - La revolución del móvil',
            'duration': 3496.948,
        },
        'params': {
            'skip_download': True,
        },
    }

    def _real_extract(self, url):
        page_id = self._match_id(url)
        webpage = self._download_webpage(url, page_id)

        alacarta_url = self._search_regex(
            r'data-location="alacarta_videos"[^<]+url&quot;:&quot;(http://www\.rtve\.es/alacarta.+?)&',
            webpage, 'alacarta url', default=None)
        if alacarta_url is None:
            raise ExtractorError(
                'The webpage doesn\'t contain any video', expected=True)

        return self.url_result(alacarta_url, ie=RTVEALaCartaIE.ie_key())
