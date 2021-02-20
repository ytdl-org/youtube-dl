# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import parse_iso8601


class GediDigitalIE(InfoExtractor):
    _VALID_URL = r'''(?x)https?://video\.
                    (?:
                        (?:espresso\.)?repubblica
                        |lastampa
                        |ilsecoloxix
                        |iltirreno
                        |messaggeroveneto
                        |ilpiccolo
                        |gazzettadimantova
                        |mattinopadova
                        |laprovinciapavese
                        |tribunatreviso
                        |nuovavenezia
                        |gazzettadimodena
                        |lanuovaferrara
                        |corrierealpi
                        |lasentinella
                    )
                    (?:\.gelocal)?\.it/.+?/(?P<id>[\d/]+)(?:\?|\&|$)'''
    _TESTS = [{
        'url': 'https://video.lastampa.it/politica/il-paradosso-delle-regionali-la-lega-vince-ma-sembra-aver-perso/121559/121683',
        'md5': '84658d7fb9e55a6e57ecc77b73137494',
        'info_dict': {
            'id': '121559/121683',
            'ext': 'mp4',
            'title': 'Il paradosso delle Regionali: ecco perché la Lega vince ma sembra aver perso',
            'description': 'md5:de7f4d6eaaaf36c153b599b10f8ce7ca',
            'thumbnail': r're:^https://www\.repstatic\.it/video/photo/.+?-thumb-social-play\.jpg$',
            'timestamp': 1600788168,
            'upload_date': '20200922',
        },
    }, {
        'url': 'https://video.repubblica.it/motori/record-della-pista-a-spa-francorchamps-la-pagani-huayra-roadster-bc-stupisce/367415/367963',
        'md5': 'e763b94b7920799a0e0e23ffefa2d157',
        'info_dict': {
            'id': '367415/367963',
            'ext': 'mp4',
            'title': 'Record della pista a Spa Francorchamps, la Pagani Huayra Roadster BC stupisce',
            'description': 'md5:5deb503cefe734a3eb3f07ed74303920',
            'thumbnail': r're:^https://www\.repstatic\.it/video/photo/.+?-thumb-social-play\.jpg$',
            'timestamp': 1600531032,
            'upload_date': '20200919',
        },
    }, {
        'url': 'https://video.ilsecoloxix.it/sport/cassani-e-i-brividi-azzurri-ai-mondiali-di-imola-qui-mi-sono-innamorato-del-ciclismo-da-ragazzino-incredibile-tornarci-da-ct/66184/66267',
        'md5': 'e48108e97b1af137d22a8469f2019057',
        'info_dict': {
            'id': '66184/66267',
            'ext': 'mp4',
            'title': 'Cassani e i brividi azzurri ai Mondiali di Imola: \'Qui mi sono innamorato del ciclismo da ragazzino, incredibile tornarci da ct\'',
            'description': 'md5:fc9c50894f70a2469bb9b54d3d0a3d3b',
            'thumbnail': r're:^https://www\.repstatic\.it/video/photo/.+?-thumb-social-play\.jpg$',
            'timestamp': 1600852553,
            'upload_date': '20200923',
        },
    }, {
        'url': 'https://video.iltirreno.gelocal.it/sport/dentro-la-notizia-ferrari-cosa-succede-a-maranello/141059/142723',
        'md5': 'a6e39f3bdc1842bbd92abbbbef230817',
        'info_dict': {
            'id': '141059/142723',
            'ext': 'mp4',
            'title': 'Dentro la notizia - Ferrari, cosa succede a Maranello',
            'description': 'md5:9907d65b53765681fa3a0b3122617c1f',
            'thumbnail': r're:^https://www\.repstatic\.it/video/photo/.+?-thumb-social-play\.jpg$',
            'timestamp': 1600847536,
            'upload_date': '20200923',
        },
    }, {
        'url': 'https://video.espresso.repubblica.it/embed/tutti-i-video/01-ted-villa/14772/14870&width=640&height=360',
        'md5': 'ca3323b47c94cac92fff03eef0387d97',
        'info_dict': {
            'id': '14772/14870',
            'ext': 'mp4',
            'title': 'Festival EMERGENCY, Villa: «La buona informazione aiuta la salute»',
            'description': 'md5:2bce954d278248f3c950be355b7c2226',
            'thumbnail': r're:^https://www\.repstatic\.it/video/photo/.+?-thumb-social-play\.jpg$',
            'timestamp': 1602159940,
            'upload_date': '20201008',
        },
    }, {
        'url': 'https://video.messaggeroveneto.gelocal.it/locale/maria-giovanna-elmi-covid-vaccino/138155/139268',
        'only_matching': True,
    }, {
        'url': 'https://video.ilpiccolo.gelocal.it/dossier/big-john/dinosauro-big-john-al-via-le-visite-guidate-a-trieste/135226/135751',
        'only_matching': True,
    }, {
        'url': 'https://video.gazzettadimantova.gelocal.it/locale/dal-ponte-visconteo-di-valeggio-l-and-8217sos-dei-ristoratori-aprire-anche-a-cena/137310/137818',
        'only_matching': True,
    }, {
        'url': 'https://video.mattinopadova.gelocal.it/dossier/coronavirus-in-veneto/covid-a-vo-un-anno-dopo-un-cuore-tricolore-per-non-dimenticare/138402/138964',
        'only_matching': True,
    }, {
        'url': 'https://video.laprovinciapavese.gelocal.it/locale/mede-zona-rossa-via-alle-vaccinazioni-per-gli-over-80/137545/138120',
        'only_matching': True,
    }, {
        'url': 'https://video.tribunatreviso.gelocal.it/dossier/coronavirus-in-veneto/ecco-le-prima-vaccinazioni-di-massa-nella-marca/134485/135024',
        'only_matching': True,
    }, {
        'url': 'https://video.nuovavenezia.gelocal.it/locale/camion-troppo-alto-per-il-ponte-ferroviario-perde-il-carico/135734/136266',
        'only_matching': True,
    }, {
        'url': 'https://video.gazzettadimodena.gelocal.it/locale/modena-scoperta-la-proteina-che-predice-il-livello-di-gravita-del-covid/139109/139796',
        'only_matching': True,
    }, {
        'url': 'https://video.lanuovaferrara.gelocal.it/locale/due-bombole-di-gpl-aperte-e-abbandonate-i-vigili-bruciano-il-gas/134391/134957',
        'only_matching': True,
    }, {
        'url': 'https://video.corrierealpi.gelocal.it/dossier/cortina-2021-i-mondiali-di-sci-alpino/mondiali-di-sci-il-timelapse-sulla-splendida-olympia/133760/134331',
        'only_matching': True,
    }, {
        'url': 'https://video.lasentinella.gelocal.it/locale/vestigne-centra-un-auto-e-si-ribalta/138931/139466',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)

        webpage = self._download_webpage(url, video_id)
        player_data = re.findall(
            r'''PlayerFactory\.setParam\('(?P<type>format|param)',\s*'(?P<name>(?:audio|video|image).*?)',\s*'(?P<val>.+?)'\);''',
            webpage)

        formats = []
        thumb = None

        for t, n, v in player_data:
            if t == 'format':
                if n == 'video-hls-vod-ak':
                    formats.extend(self._extract_akamai_formats(
                        v, video_id, {'http': 'media.gedidigital.it'}))
                if n == 'audio-hls-vod':
                    formats.extend(self._extract_m3u8_formats(
                        v, video_id, 'm4a', m3u8_id='audio-hls', fatal=False))
                if n == 'audio-rrtv-mp3':
                    formats.append({
                        'format_id': 'audio-mp3',
                        'url': v,
                        'tbr': 128,
                        'ext': 'mp3',
                        'vcodec': 'none',
                        'acodec': 'mp3',
                    })
            elif t == 'param':
                if n in ['image_full_play', 'image_full', 'image']:
                    thumb = v

        self._sort_formats(formats)

        return {
            'id': video_id,
            'title': self._html_search_meta('twitter:title', webpage) or self._og_search_title(webpage),
            'description': self._html_search_meta(
                ['twitter:description', 'og:description', 'description'],
                webpage, default=None),
            'timestamp': parse_iso8601(self._og_search_property(
                ['published_time', 'modified_time'],
                webpage, default='').strip()),
            'thumbnail': thumb or self._og_search_thumbnail(webpage),
            'formats': formats,
        }
