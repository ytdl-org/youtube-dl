# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..compat import (
    compat_str,
    compat_urllib_parse_urlparse,
)
from ..utils import (
    int_or_none,
    parse_duration,
    parse_iso8601,
    unescapeHTML,
    xpath_text,
)


class RTSIE(InfoExtractor):
    IE_DESC = 'RTS.ch'
    _VALID_URL = r'''(?x)
                    (?:
                        rts:(?P<rts_id>\d+)|
                        https?://
                            (?:www\.)?rts\.ch/
                            (?:
                                (?:[^/]+/){2,}(?P<id>[0-9]+)-(?P<display_id>.+?)\.html|
                                play/tv/[^/]+/video/(?P<display_id_new>.+?)\?id=(?P<id_new>[0-9]+)
                            )
                    )'''

    _TESTS = [
        {
            'url': 'http://www.rts.ch/archives/tv/divers/3449373-les-enfants-terribles.html',
            'md5': '753b877968ad8afaeddccc374d4256a5',
            'info_dict': {
                'id': '3449373',
                'display_id': 'les-enfants-terribles',
                'ext': 'mp4',
                'duration': 1488,
                'title': 'Les Enfants Terribles',
                'description': 'France Pommier et sa soeur Luce Feral, les deux filles de ce groupe de 5.',
                'uploader': 'Divers',
                'upload_date': '19680921',
                'timestamp': -40280400,
                'thumbnail': 're:^https?://.*\.image',
                'view_count': int,
            },
        },
        {
            'url': 'http://www.rts.ch/emissions/passe-moi-les-jumelles/5624067-entre-ciel-et-mer.html',
            'md5': 'c148457a27bdc9e5b1ffe081a7a8337b',
            'info_dict': {
                'id': '5624067',
                'display_id': 'entre-ciel-et-mer',
                'ext': 'mp4',
                'duration': 3720,
                'title': 'Les yeux dans les cieux - Mon homard au Canada',
                'description': 'md5:d22ee46f5cc5bac0912e5a0c6d44a9f7',
                'uploader': 'Passe-moi les jumelles',
                'upload_date': '20140404',
                'timestamp': 1396635300,
                'thumbnail': 're:^https?://.*\.image',
                'view_count': int,
            },
        },
        {
            'url': 'http://www.rts.ch/video/sport/hockey/5745975-1-2-kloten-fribourg-5-2-second-but-pour-gotteron-par-kwiatowski.html',
            'md5': 'b4326fecd3eb64a458ba73c73e91299d',
            'info_dict': {
                'id': '5745975',
                'display_id': '1-2-kloten-fribourg-5-2-second-but-pour-gotteron-par-kwiatowski',
                'ext': 'mp4',
                'duration': 48,
                'title': '1/2, Kloten - Fribourg (5-2): second but pour Gottéron par Kwiatowski',
                'description': 'Hockey - Playoff',
                'uploader': 'Hockey',
                'upload_date': '20140403',
                'timestamp': 1396556882,
                'thumbnail': 're:^https?://.*\.image',
                'view_count': int,
            },
            'skip': 'Blocked outside Switzerland',
        },
        {
            'url': 'http://www.rts.ch/video/info/journal-continu/5745356-londres-cachee-par-un-epais-smog.html',
            'md5': '9bb06503773c07ce83d3cbd793cebb91',
            'info_dict': {
                'id': '5745356',
                'display_id': 'londres-cachee-par-un-epais-smog',
                'ext': 'mp4',
                'duration': 33,
                'title': 'Londres cachée par un épais smog',
                'description': 'Un important voile de smog recouvre Londres depuis mercredi, provoqué par la pollution et du sable du Sahara.',
                'uploader': 'Le Journal en continu',
                'upload_date': '20140403',
                'timestamp': 1396537322,
                'thumbnail': 're:^https?://.*\.image',
                'view_count': int,
            },
        },
        {
            'url': 'http://www.rts.ch/audio/couleur3/programmes/la-belle-video-de-stephane-laurenceau/5706148-urban-hippie-de-damien-krisl-03-04-2014.html',
            'md5': 'dd8ef6a22dff163d063e2a52bc8adcae',
            'info_dict': {
                'id': '5706148',
                'display_id': 'urban-hippie-de-damien-krisl-03-04-2014',
                'ext': 'mp3',
                'duration': 123,
                'title': '"Urban Hippie", de Damien Krisl',
                'description': 'Des Hippies super glam.',
                'upload_date': '20140403',
                'timestamp': 1396551600,
            },
        },
        {
            'url': 'http://www.rts.ch/play/tv/-/video/le-19h30?id=6348260',
            'md5': '968777c8779e5aa2434be96c54e19743',
            'info_dict': {
                'id': '6348260',
                'display_id': 'le-19h30',
                'ext': 'mp4',
                'duration': 1796,
                'title': 'Le 19h30',
                'description': '',
                'uploader': 'Le 19h30',
                'upload_date': '20141201',
                'timestamp': 1417458600,
                'thumbnail': 're:^https?://.*\.image',
                'view_count': int,
            },
        },
        {
            # article with videos on rhs
            'url': 'http://www.rts.ch/sport/hockey/6693917-hockey-davos-decroche-son-31e-titre-de-champion-de-suisse.html',
            'info_dict': {
                'id': '6693917',
                'title': 'Hockey: Davos décroche son 31e titre de champion de Suisse',
            },
            'playlist_mincount': 5,
        },
        {
            'url': 'http://www.rts.ch/play/tv/le-19h30/video/le-chantier-du-nouveau-parlement-vaudois-a-permis-une-trouvaille-historique?id=6348280',
            'only_matching': True,
        }
    ]

    def _real_extract(self, url):
        m = re.match(self._VALID_URL, url)
        video_id = m.group('rts_id') or m.group('id') or m.group('id_new')
        display_id = m.group('display_id') or m.group('display_id_new')

        def download_json(internal_id):
            return self._download_json(
                'http://www.rts.ch/a/%s.html?f=json/article' % internal_id,
                display_id)

        all_info = download_json(video_id)

        # video_id extracted out of URL is not always a real id
        if 'video' not in all_info and 'audio' not in all_info:
            page = self._download_webpage(url, display_id)

            # article with videos on rhs
            videos = re.findall(
                r'<article[^>]+class="content-item"[^>]*>\s*<a[^>]+data-video-urn="urn:rts:video:(\d+)"',
                page)
            if videos:
                entries = [self.url_result('rts:%s' % video_urn, 'RTS') for video_urn in videos]
                return self.playlist_result(entries, video_id, self._og_search_title(page))

            internal_id = self._html_search_regex(
                r'<(?:video|audio) data-id="([0-9]+)"', page,
                'internal video id')
            all_info = download_json(internal_id)

        info = all_info['video']['JSONinfo'] if 'video' in all_info else all_info['audio']

        upload_timestamp = parse_iso8601(info.get('broadcast_date'))
        duration = info.get('duration') or info.get('cutout') or info.get('cutduration')
        if isinstance(duration, compat_str):
            duration = parse_duration(duration)
        view_count = info.get('plays')
        thumbnail = unescapeHTML(info.get('preview_image_url'))

        def extract_bitrate(url):
            return int_or_none(self._search_regex(
                r'-([0-9]+)k\.', url, 'bitrate', default=None))

        formats = []
        for format_id, format_url in info['streams'].items():
            if format_url.endswith('.f4m'):
                token = self._download_xml(
                    'http://tp.srgssr.ch/token/akahd.xml?stream=%s/*' % compat_urllib_parse_urlparse(format_url).path,
                    video_id, 'Downloading %s token' % format_id)
                auth_params = xpath_text(token, './/authparams', 'auth params')
                if not auth_params:
                    continue
                formats.extend(self._extract_f4m_formats(
                    '%s?%s&hdcore=3.4.0&plugin=aasp-3.4.0.132.66' % (format_url, auth_params),
                    video_id, f4m_id=format_id))
            elif format_url.endswith('.m3u8'):
                formats.extend(self._extract_m3u8_formats(
                    format_url, video_id, 'mp4', m3u8_id=format_id))
            else:
                formats.append({
                    'format_id': format_id,
                    'url': format_url,
                    'tbr': extract_bitrate(format_url),
                })

        if 'media' in info:
            formats.extend([{
                'format_id': '%s-%sk' % (media['ext'], media['rate']),
                'url': 'http://download-video.rts.ch/%s' % media['url'],
                'tbr': media['rate'] or extract_bitrate(media['url']),
            } for media in info['media'] if media.get('rate')])

        self._check_formats(formats, video_id)
        self._sort_formats(formats)

        return {
            'id': video_id,
            'display_id': display_id,
            'formats': formats,
            'title': info['title'],
            'description': info.get('intro'),
            'duration': duration,
            'view_count': view_count,
            'uploader': info.get('programName'),
            'timestamp': upload_timestamp,
            'thumbnail': thumbnail,
        }
