# coding: utf-8
from __future__ import unicode_literals

import re

from .srgssr import SRGSSRIE
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


class RTSIE(SRGSSRIE):
    IE_DESC = 'RTS.ch'
    _VALID_URL = r'rts:(?P<rts_id>\d+)|https?://(?:www\.)?rts\.ch/(?:[^/]+/){2,}(?P<id>[0-9]+)-(?P<display_id>.+?)\.html'

    _TESTS = [
        {
            'url': 'http://www.rts.ch/archives/tv/divers/3449373-les-enfants-terribles.html',
            'md5': 'f254c4b26fb1d3c183793d52bc40d3e7',
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
            'params': {
                # m3u8 download
                'skip_download': True,
            }
        },
        {
            'url': 'http://www.rts.ch/emissions/passe-moi-les-jumelles/5624067-entre-ciel-et-mer.html',
            'md5': 'f1077ac5af686c76528dc8d7c5df29ba',
            'info_dict': {
                'id': '5742494',
                'display_id': '5742494',
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
            'params': {
                # m3u8 download
                'skip_download': True,
            }
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
            'md5': '9f713382f15322181bb366cc8c3a4ff0',
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
            'params': {
                # m3u8 download
                'skip_download': True,
            }
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
            # article with videos on rhs
            'url': 'http://www.rts.ch/sport/hockey/6693917-hockey-davos-decroche-son-31e-titre-de-champion-de-suisse.html',
            'info_dict': {
                'id': '6693917',
                'title': 'Hockey: Davos décroche son 31e titre de champion de Suisse',
            },
            'playlist_mincount': 5,
        }
    ]

    def _real_extract(self, url):
        m = re.match(self._VALID_URL, url)
        media_id = m.group('rts_id') or m.group('id')
        display_id = m.group('display_id') or media_id

        def download_json(internal_id):
            return self._download_json(
                'http://www.rts.ch/a/%s.html?f=json/article' % internal_id,
                display_id)

        all_info = download_json(media_id)

        # media_id extracted out of URL is not always a real id
        if 'video' not in all_info and 'audio' not in all_info:
            page = self._download_webpage(url, display_id)

            # article with videos on rhs
            videos = re.findall(
                r'<article[^>]+class="content-item"[^>]*>\s*<a[^>]+data-video-urn="urn:([^"]+)"',
                page)
            if not videos:
                videos = re.findall(
                    r'(?s)<iframe[^>]+class="srg-player"[^>]+src="[^"]+urn:([^"]+)"',
                    page)
            if videos:
                entries = [self.url_result('srgssr:%s' % video_urn, 'SRGSSR') for video_urn in videos]
                return self.playlist_result(entries, media_id, self._og_search_title(page))

            internal_id = self._html_search_regex(
                r'<(?:video|audio) data-id="([0-9]+)"', page,
                'internal video id')
            all_info = download_json(internal_id)

        media_type = 'video' if 'video' in all_info else 'audio'

        # check for errors
        self.get_media_data('rts', media_type, media_id)

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
            if format_id == 'hds_sd' and 'hds' in info['streams']:
                continue
            if format_id == 'hls_sd' and 'hls' in info['streams']:
                continue
            if format_url.endswith('.f4m'):
                token = self._download_xml(
                    'http://tp.srgssr.ch/token/akahd.xml?stream=%s/*' % compat_urllib_parse_urlparse(format_url).path,
                    media_id, 'Downloading %s token' % format_id)
                auth_params = xpath_text(token, './/authparams', 'auth params')
                if not auth_params:
                    continue
                formats.extend(self._extract_f4m_formats(
                    '%s?%s&hdcore=3.4.0&plugin=aasp-3.4.0.132.66' % (format_url, auth_params),
                    media_id, f4m_id=format_id, fatal=False))
            elif format_url.endswith('.m3u8'):
                formats.extend(self._extract_m3u8_formats(
                    format_url, media_id, 'mp4', 'm3u8_native', m3u8_id=format_id, fatal=False))
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

        self._check_formats(formats, media_id)
        self._sort_formats(formats)

        return {
            'id': media_id,
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
