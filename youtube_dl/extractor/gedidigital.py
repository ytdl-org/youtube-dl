# coding: utf-8
from __future__ import unicode_literals

import re
from var_dump import var_dump

from .common import InfoExtractor


class GediDigitalBaseIE(InfoExtractor):
    @staticmethod
    def _clean_audio_fmts(formats):
        unique_formats = []
        for f in formats:
            if 'acodec' in f:
                unique_formats.append(f)
        formats[:] = unique_formats

    def _real_extract(self, url):
        u = re.match(self._VALID_URL, url)
        self.IE_NAME = u.group('iename') if u.group('iename') else 'gedi'
        video_id = self._match_id(url)

        webpage = self._download_webpage(url, video_id)
        player_data = re.findall(
            r'PlayerFactory\.setParam\(\'(?P<type>.+?)\',\s*\'(?P<name>.+?)\',\s*\'(?P<val>.+?)\'\);',
            webpage)

        formats = []
        audio_fmts = []
        hls_fmts = []
        http_fmts = []
        title = ''
        thumb = ''

        fmt_reg = r'(?P<t>video|audio)-(?P<p>rrtv|hls)-(?P<h>[\w\d]+)(?:-(?P<br>[\w\d]+))?$'
        br_reg = r'video-rrtv-(?P<br>\d+)-'
        for t, n, v in player_data:
            if t == 'format':
                m = re.match(fmt_reg, n)
                if m:
                    # audio formats
                    if m.group('t') == 'audio':
                        if m.group('p') == 'hls':
                            audio_fmts.extend(self._extract_m3u8_formats(
                                v, video_id, 'm4a', m3u8_id='hls', fatal=False))
                        elif m.group('p') == 'rrtv':
                            audio_fmts.append({
                                'format_id': 'mp3',
                                'url': v,
                                'tbr': 128,
                                'ext': 'mp3',
                                'vcodec': 'none',
                                'acodec': 'mp3',
                            })

                    # video formats
                    elif m.group('t') == 'video':
                        # hls manifest video
                        if m.group('p') == 'hls':
                            hls_fmts.extend(self._extract_m3u8_formats(
                                v, video_id, 'mp4', m3u8_id='hls', fatal=False))
                        # direct mp4 video
                        elif m.group('p') == 'rrtv':
                            if not m.group('br'):
                                mm = re.search(br_reg, v)
                            http_fmts.append({
                                'format_id': 'https-' + m.group('h'),
                                'protocol': 'https',
                                'url': v,
                                'tbr': int(m.group('br')) if m.group('br') else
                                (int(mm.group('br')) if mm.group('br') else 0),
                                'height': int(m.group('h'))
                            })

            elif t == 'param':
                if n == 'videotitle':
                    title = v
                if n == 'image_full_play':
                    thumb = v

        title = re.sub(r'\s*-\s*La Stampa', '', self._og_search_title(webpage)) if title == '' else title

        if audio_fmts:
            self._clean_audio_fmts(audio_fmts)
            self._sort_formats(audio_fmts)
        if hls_fmts:
            self._sort_formats(hls_fmts)
        if http_fmts:
            self._sort_formats(http_fmts)

        formats.extend(audio_fmts)
        formats.extend(hls_fmts)
        formats.extend(http_fmts)

        return {
            'id': video_id,
            'title': title,
            'description': self._html_search_meta('twitter:description', webpage),
            'thumbnail': thumb,
            'formats': formats,
        }


class GediDigitalIE(GediDigitalBaseIE):
    IE_NAME = ''
    _VALID_URL = r'''(?x)https://video\.
                    (?P<iename>
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
                    (?:\.gelocal)?\.it/.+?/(?P<id>[\d/]+)$'''
    _TESTS = [{
        'url': 'https://video.lastampa.it/politica/il-paradosso-delle-regionali-la-lega-vince-ma-sembra-aver-perso/121559/121683',
        'md5': '84658d7fb9e55a6e57ecc77b73137494',
        'info_dict': {
            'id': '121559/121683',
            'ext': 'mp4',
            'title': 'Il paradosso delle Regionali: ecco perché la Lega vince ma sembra aver perso',
            'description': 'md5:de7f4d6eaaaf36c153b599b10f8ce7ca',
            'thumbnail': 'https://www.repstatic.it/video/photo/2020/09/22/731397/731397-thumb-social-play.jpg',
        },
    }, {
        'url': 'https://video.repubblica.it/motori/record-della-pista-a-spa-francorchamps-la-pagani-huayra-roadster-bc-stupisce/367415/367963',
        'md5': 'e763b94b7920799a0e0e23ffefa2d157',
        'info_dict': {
            'id': '367415/367963',
            'ext': 'mp4',
            'title': 'Record della pista a Spa Francorchamps, la Pagani Huayra Roadster BC stupisce',
            'description': 'md5:5deb503cefe734a3eb3f07ed74303920',
            'thumbnail': 'https://www.repstatic.it/video/photo/2020/09/19/730799/730799-thumb-social-play.jpg',
        },
    }, {
        'url': 'https://video.ilsecoloxix.it/sport/cassani-e-i-brividi-azzurri-ai-mondiali-di-imola-qui-mi-sono-innamorato-del-ciclismo-da-ragazzino-incredibile-tornarci-da-ct/66184/66267',
        'md5': 'e48108e97b1af137d22a8469f2019057',
        'info_dict': {
            'id': '66184/66267',
            'ext': 'mp4',
            'title': 'Cassani e i brividi azzurri ai Mondiali di Imola: \\"Qui mi sono innamorato del ciclismo da ragazzino, incredibile tornarci da ct\\"',
            'description': 'md5:fc9c50894f70a2469bb9b54d3d0a3d3b',
            'thumbnail': 'https://www.repstatic.it/video/photo/2020/09/23/731520/731520-thumb-social-play.jpg',
        },
    }, {
        'url': 'https://video.iltirreno.gelocal.it/sport/dentro-la-notizia-ferrari-cosa-succede-a-maranello/141059/142723',
        'md5': 'a6e39f3bdc1842bbd92abbbbef230817',
        'info_dict': {
            'id': '141059/142723',
            'ext': 'mp4',
            'title': 'Dentro la notizia - Ferrari, cosa succede a Maranello',
            'description': 'md5:9907d65b53765681fa3a0b3122617c1f',
            'thumbnail': 'https://www.repstatic.it/video/photo/2020/09/23/731504/731504-thumb-social-play.jpg',
        },
    }, {
        'url': 'https://video.messaggeroveneto.gelocal.it/sport/dentro-la-notizia-ferrari-cosa-succede-a-maranello/133362/134466',
        'only_matching': True,
    }, {
        'url': 'https://video.ilpiccolo.gelocal.it/sport/dentro-la-notizia-ferrari-cosa-succede-a-maranello/133362/134466',
        'only_matching': True,
    }, {
        'url': 'https://video.gazzettadimantova.gelocal.it/sport/dentro-la-notizia-ferrari-cosa-succede-a-maranello/133362/134466',
        'only_matching': True,
    }, {
        'url': 'https://video.mattinopadova.gelocal.it/sport/dentro-la-notizia-ferrari-cosa-succede-a-maranello/133362/134466',
        'only_matching': True,
    }, {
        'url': 'https://video.laprovinciapavese.gelocal.it/sport/dentro-la-notizia-ferrari-cosa-succede-a-maranello/133362/134466',
        'only_matching': True,
    }, {
        'url': 'https://video.tribunatreviso.gelocal.it/sport/dentro-la-notizia-ferrari-cosa-succede-a-maranello/133362/134466',
        'only_matching': True,
    }, {
        'url': 'https://video.nuovavenezia.gelocal.it/sport/dentro-la-notizia-ferrari-cosa-succede-a-maranello/133362/134466',
        'only_matching': True,
    }, {
        'url': 'https://video.gazzettadimodena.gelocal.it/sport/dentro-la-notizia-ferrari-cosa-succede-a-maranello/133362/134466',
        'only_matching': True,
    }, {
        'url': 'https://video.lanuovaferrara.gelocal.it/sport/dentro-la-notizia-ferrari-cosa-succede-a-maranello/133362/134466',
        'only_matching': True,
    }, {
        'url': 'https://video.corrierealpi.gelocal.it/sport/dentro-la-notizia-ferrari-cosa-succede-a-maranello/133362/134466',
        'only_matching': True,
    }, {
        'url': 'https://video.lasentinella.gelocal.it/sport/dentro-la-notizia-ferrari-cosa-succede-a-maranello/133362/134466',
        'only_matching': True,
    }]
