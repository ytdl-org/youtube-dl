# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..compat import compat_str
from ..utils import int_or_none


class GediDigitalIE(InfoExtractor):
    IE_NAME = ''
    _VALID_URL = r'''(?x)https?://video\.
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
        },
    }, {
        'url': 'https://video.ilsecoloxix.it/sport/cassani-e-i-brividi-azzurri-ai-mondiali-di-imola-qui-mi-sono-innamorato-del-ciclismo-da-ragazzino-incredibile-tornarci-da-ct/66184/66267',
        'md5': 'e48108e97b1af137d22a8469f2019057',
        'info_dict': {
            'id': '66184/66267',
            'ext': 'mp4',
            'title': 'Cassani e i brividi azzurri ai Mondiali di Imola: \\"Qui mi sono innamorato del ciclismo da ragazzino, incredibile tornarci da ct\\"',
            'description': 'md5:fc9c50894f70a2469bb9b54d3d0a3d3b',
            'thumbnail': r're:^https://www\.repstatic\.it/video/photo/.+?-thumb-social-play\.jpg$',
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
        },
    }, {
        'url': 'https://video.espresso.repubblica.it/embed/tutti-i-video/01-ted-villa/14772/14870&width=640&height=360',
        'md5': 'ca3323b47c94cac92fff03eef0387d97',
        'info_dict': {
            'id': '14772/14870',
            'ext': 'mp4',
            'title': 'Festival EMERGENCY, Villa: «La buona informazione aiuta la salute» (14772-14870)',
            'description': 'md5:2bce954d278248f3c950be355b7c2226',
            'thumbnail': r're:^https://www\.repstatic\.it/video/photo/.+?-thumb-social-play\.jpg$',
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

    @staticmethod
    def _clean_audio_fmts(formats):
        # remove duplicates audio formats
        unique_formats = []
        for f in formats:
            if 'acodec' in f:
                unique_formats.append(f)
        formats[:] = unique_formats

    @staticmethod
    def _generate_http_urls(mp4, formats):
        _QUALITY = {
            # tbr: w, h
            '200': [428, 240],
            '400': [428, 240],
            '650': [640, 360],
            '1200': [640, 360],
            '1800': [854, 480],
            '2500': [1280, 720],
            '3500': [1280, 720],
            '4500': [1920, 1080]
        }
        _PATTERN = r'(rrtv-([\d\,]+)-)'

        def get_format_info(tbr):
            br = int_or_none(tbr)
            if len(formats) == 1 and not br:
                br = formats[0].get('tbr')

            for f in formats:
                if f.get('tbr'):
                    if (br - br / 100 * 10) <= f['tbr'] <= (br + br / 100 * 10):
                        return [
                            f.get('width'),
                            f.get('height'),
                            f['tbr']
                        ]
            return [None, None, None]

        mobj = re.search(_PATTERN, mp4.get('mp4') or '')
        if not mobj:
            return None
        pattern = mobj.group(1)

        qualities = re.search(_PATTERN, mp4.get('manifest') or '')
        if qualities:
            qualities = qualities.group(2)
            qualities = qualities.split(',') if qualities else ['.']
            qualities = [i for i in qualities if i]
        else:
            qualities = [mobj.group(2)]

        http_formats = []
        for q in qualities:
            w, h, t = get_format_info(q)
            http_formats.append({
                'url': mp4['mp4'].replace(pattern, 'rrtv-%s-' % q),
                'width': w or _QUALITY[q][0],
                'height': h or _QUALITY[q][1],
                'tbr': t or int(q),
                'protocol': 'https',
                'format_id': 'https-%s' % q,
            })
        return http_formats

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
        title = None
        thumb = None
        mp4 = {}

        for t, n, v in player_data:
            if t == 'format':
                if n == 'mp4':
                    mp4.update({'mp4': v})
                if n == 'video-hls-vod-ak':
                    mp4.update({'manifest': v})
                    formats.extend(self._extract_akamai_formats(
                        v, video_id, {'http': 'media.gedidigital.it'}))
                if n == 'audio-hls-vod':
                    audio_fmts.extend(self._extract_m3u8_formats(
                        v, video_id, 'm4a', m3u8_id='audio-hls', fatal=False))
                if n == 'audio-rrtv-mp3':
                    audio_fmts.append({
                        'format_id': 'mp3',
                        'url': v,
                        'tbr': 128,
                        'ext': 'mp3',
                        'vcodec': 'none',
                        'acodec': 'mp3',
                    })
            elif t == 'param':
                if n == 'videotitle':
                    title = v
                if n in ['image_full_play', 'image_full', 'image']:
                    thumb = v

        title = self._og_search_title(webpage) if not title else title

        # clean weird char
        title = compat_str(title).encode('utf8', 'replace').replace(b'\xc3\x82', b'').decode('utf8', 'replace')

        self._clean_audio_fmts(audio_fmts)
        formats.extend(audio_fmts)

        if mp4:
            formats.extend(self._generate_http_urls(mp4, formats) or [])

        self._sort_formats(formats)

        return {
            'id': video_id,
            'title': title,
            'description': self._html_search_meta('twitter:description', webpage),
            'thumbnail': thumb,
            'formats': formats,
        }
