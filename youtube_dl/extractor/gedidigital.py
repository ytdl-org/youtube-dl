# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import int_or_none


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
        'md5': '1e9bbbfb7c563b6858376fa6e4211b30',
        'info_dict': {
            'id': '121559/121683',
            'ext': 'mp4',
            'title': 'Il paradosso delle Regionali: ecco perché la Lega vince ma sembra aver perso',
            'description': 'md5:de7f4d6eaaaf36c153b599b10f8ce7ca',
            'thumbnail': r're:^https://www\.repstatic\.it/video/photo/.+?-thumb-full-.+?\.jpg$',
        },
    }, {
        'url': 'https://video.espresso.repubblica.it/embed/tutti-i-video/01-ted-villa/14772/14870&width=640&height=360',
        'only_matching': True,
    }, {
        'url': 'https://video.repubblica.it/motori/record-della-pista-a-spa-francorchamps-la-pagani-huayra-roadster-bc-stupisce/367415/367963',
        'only_matching': True,
    }, {
        'url': 'https://video.ilsecoloxix.it/sport/cassani-e-i-brividi-azzurri-ai-mondiali-di-imola-qui-mi-sono-innamorato-del-ciclismo-da-ragazzino-incredibile-tornarci-da-ct/66184/66267',
        'only_matching': True,
    }, {
        'url': 'https://video.iltirreno.gelocal.it/sport/dentro-la-notizia-ferrari-cosa-succede-a-maranello/141059/142723',
        'only_matching': True,
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
            r'''PlayerFactory\.setParam\('(?P<type>format|param)',\s*'(?P<name>(?:audio|video|image|mp4).*?)',\s*'(?P<val>.+?)'\);''',
            webpage)

        formats = []
        thumb = None
        for t, n, v in player_data:
            if t == 'format':
                # http direct formats
                fmt = re.match(r'(?:video|mp4)(?:-rrtv-)?(\d+)?-?(\d+)?$', n)
                if fmt:
                    formats.append({
                        'format_id': n if 'video' in n else 'video-%s' % n,
                        'url': v,
                        'ext': 'mp4',
                        'protocol': 'https',
                        'height': int_or_none(fmt.group(1)) or 360,
                        'tbr': int_or_none(fmt.group(2)) or (
                            4500 if fmt.group(1) == '1080' else 650),
                    })
                    continue
                # hls formats
                fmt = re.match(r'(video|audio)-(hls|ipad)-', n)
                if fmt:
                    ext = 'mp4' if fmt.group(1) == 'video' else 'm4a'
                    formats.extend(self._extract_m3u8_formats(
                        v, video_id, ext, m3u8_id=n, fatal=False))
                    continue
                # hds formats
                if 'video-hds-' in n:
                    f4m_formats = self._extract_f4m_formats(
                        '%s?hdcore=3.7.0' % v, video_id, f4m_id=n, fatal=False)
                    for entry in f4m_formats:
                        entry.update({'extra_param_to_segment_url': 'hdcore=3.7.0'})
                    formats.extend(f4m_formats)
                    continue
                # mp3 audio
                if n == 'audio-rrtv-mp3':
                    formats.append({
                        'format_id': 'audio-mp3',
                        'url': v,
                        'tbr': 128,
                        'ext': 'mp3',
                        'vcodec': 'none',
                        'acodec': 'mp3',
                    })
            elif t == 'param' and n in ['image_full', 'image']:
                thumb = v

        self._sort_formats(formats)

        return {
            'id': video_id,
            'title': self._html_search_meta('twitter:title', webpage) or self._og_search_title(webpage),
            'description': self._html_search_meta(
                ['twitter:description', 'og:description', 'description'],
                webpage, default=None),
            'thumbnail': thumb or self._og_search_thumbnail(webpage),
            'formats': formats,
        }
