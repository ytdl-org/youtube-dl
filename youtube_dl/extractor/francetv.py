# coding: utf-8

from __future__ import unicode_literals

import re
import json

from .common import InfoExtractor
from ..compat import compat_urlparse
from ..utils import (
    clean_html,
    ExtractorError,
    int_or_none,
    parse_duration,
    determine_ext,
)
from .dailymotion import (
    DailymotionIE,
    DailymotionCloudIE,
)


class FranceTVBaseInfoExtractor(InfoExtractor):
    def _extract_video(self, video_id, catalogue=None):
        info = self._download_json(
            'https://sivideo.webservices.francetelevisions.fr/tools/getInfosOeuvre/v2/',
            video_id, 'Downloading video JSON', query={
                'idDiffusion': video_id,
                'catalogue': catalogue or '',
            })

        if info.get('status') == 'NOK':
            raise ExtractorError(
                '%s returned error: %s' % (self.IE_NAME, info['message']), expected=True)
        allowed_countries = info['videos'][0].get('geoblocage')
        if allowed_countries:
            georestricted = True
            geo_info = self._download_json(
                'http://geo.francetv.fr/ws/edgescape.json', video_id,
                'Downloading geo restriction info')
            country = geo_info['reponse']['geo_info']['country_code']
            if country not in allowed_countries:
                raise ExtractorError(
                    'The video is not available from your location',
                    expected=True)
        else:
            georestricted = False

        formats = []
        for video in info['videos']:
            if video['statut'] != 'ONLINE':
                continue
            video_url = video['url']
            if not video_url:
                continue
            format_id = video['format']
            ext = determine_ext(video_url)
            if ext == 'f4m':
                if georestricted:
                    # See https://github.com/rg3/youtube-dl/issues/3963
                    # m3u8 urls work fine
                    continue
                f4m_url = self._download_webpage(
                    'http://hdfauth.francetv.fr/esi/TA?url=%s' % video_url,
                    video_id, 'Downloading f4m manifest token', fatal=False)
                if f4m_url:
                    formats.extend(self._extract_f4m_formats(
                        f4m_url + '&hdcore=3.7.0&plugin=aasp-3.7.0.39.44',
                        video_id, f4m_id=format_id, fatal=False))
            elif ext == 'm3u8':
                formats.extend(self._extract_m3u8_formats(
                    video_url, video_id, 'mp4', entry_protocol='m3u8_native',
                    m3u8_id=format_id, fatal=False))
            elif video_url.startswith('rtmp'):
                formats.append({
                    'url': video_url,
                    'format_id': 'rtmp-%s' % format_id,
                    'ext': 'flv',
                })
            else:
                if self._is_valid_url(video_url, video_id, format_id):
                    formats.append({
                        'url': video_url,
                        'format_id': format_id,
                    })
        self._sort_formats(formats)

        title = info['titre']
        subtitle = info.get('sous_titre')
        if subtitle:
            title += ' - %s' % subtitle
        title = title.strip()

        subtitles = {}
        subtitles_list = [{
            'url': subformat['url'],
            'ext': subformat.get('format'),
        } for subformat in info.get('subtitles', []) if subformat.get('url')]
        if subtitles_list:
            subtitles['fr'] = subtitles_list

        return {
            'id': video_id,
            'title': title,
            'description': clean_html(info['synopsis']),
            'thumbnail': compat_urlparse.urljoin('http://pluzz.francetv.fr', info['image']),
            'duration': int_or_none(info.get('real_duration')) or parse_duration(info['duree']),
            'timestamp': int_or_none(info['diffusion']['timestamp']),
            'formats': formats,
            'subtitles': subtitles,
        }


class FranceTVIE(FranceTVBaseInfoExtractor):
    _VALID_URL = r'https?://(?:(?:www\.)?france\.tv|mobile\.france\.tv)/(?:[^/]+/)*(?P<id>[^/]+)\.html'

    _TESTS = [{
        'url': 'https://www.france.tv/france-2/13h15-le-dimanche/140921-les-mysteres-de-jesus.html',
        'info_dict': {
            'id': '157550144',
            'ext': 'mp4',
            'title': '13h15, le dimanche... - Les mystères de Jésus',
            'description': 'md5:75efe8d4c0a8205e5904498ffe1e1a42',
            'timestamp': 1494156300,
            'upload_date': '20170507',
        },
        'params': {
            # m3u8 downloads
            'skip_download': True,
        },
    }, {
        # france3
        'url': 'https://www.france.tv/france-3/des-chiffres-et-des-lettres/139063-emission-du-mardi-9-mai-2017.html',
        'only_matching': True,
    }, {
        # france4
        'url': 'https://www.france.tv/france-4/hero-corp/saison-1/134151-apres-le-calme.html',
        'only_matching': True,
    }, {
        # france5
        'url': 'https://www.france.tv/france-5/c-a-dire/saison-10/137013-c-a-dire.html',
        'only_matching': True,
    }, {
        # franceo
        'url': 'https://www.france.tv/france-o/archipels/132249-mon-ancetre-l-esclave.html',
        'only_matching': True,
    }, {
        # france2 live
        'url': 'https://www.france.tv/france-2/direct.html',
        'only_matching': True,
    }, {
        'url': 'https://www.france.tv/documentaires/histoire/136517-argentine-les-500-bebes-voles-de-la-dictature.html',
        'only_matching': True,
    }, {
        'url': 'https://www.france.tv/jeux-et-divertissements/divertissements/133965-le-web-contre-attaque.html',
        'only_matching': True,
    }, {
        'url': 'https://mobile.france.tv/france-5/c-dans-l-air/137347-emission-du-vendredi-12-mai-2017.html',
        'only_matching': True,
    }, {
        'url': 'https://www.france.tv/142749-rouge-sang.html',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        display_id = self._match_id(url)

        webpage = self._download_webpage(url, display_id)

        catalogue = None
        video_id = self._search_regex(
            r'data-main-video=(["\'])(?P<id>(?:(?!\1).)+)\1',
            webpage, 'video id', default=None, group='id')

        if not video_id:
            video_id, catalogue = self._html_search_regex(
                r'(?:href=|player\.setVideo\(\s*)"http://videos?\.francetv\.fr/video/([^@]+@[^"]+)"',
                webpage, 'video ID').split('@')
        return self._extract_video(video_id, catalogue)


class FranceTVEmbedIE(FranceTVBaseInfoExtractor):
    _VALID_URL = r'https?://embed\.francetv\.fr/*\?.*?\bue=(?P<id>[^&]+)'

    _TEST = {
        'url': 'http://embed.francetv.fr/?ue=7fd581a2ccf59d2fc5719c5c13cf6961',
        'info_dict': {
            'id': 'NI_983319',
            'ext': 'mp4',
            'title': 'Le Pen Reims',
            'upload_date': '20170505',
            'timestamp': 1493981780,
            'duration': 16,
        },
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)

        video = self._download_json(
            'http://api-embed.webservices.francetelevisions.fr/key/%s' % video_id,
            video_id)

        return self._extract_video(video['video_id'], video.get('catalog'))


class FranceTVInfoIE(FranceTVBaseInfoExtractor):
    IE_NAME = 'francetvinfo.fr'
    _VALID_URL = r'https?://(?:www|mobile|france3-regions)\.francetvinfo\.fr/(?:[^/]+/)*(?P<title>[^/?#&.]+)'

    _TESTS = [{
        'url': 'http://www.francetvinfo.fr/replay-jt/france-3/soir-3/jt-grand-soir-3-lundi-26-aout-2013_393427.html',
        'info_dict': {
            'id': '84981923',
            'ext': 'mp4',
            'title': 'Soir 3',
            'upload_date': '20130826',
            'timestamp': 1377548400,
            'subtitles': {
                'fr': 'mincount:2',
            },
        },
        'params': {
            # m3u8 downloads
            'skip_download': True,
        },
    }, {
        'url': 'http://www.francetvinfo.fr/elections/europeennes/direct-europeennes-regardez-le-debat-entre-les-candidats-a-la-presidence-de-la-commission_600639.html',
        'info_dict': {
            'id': 'EV_20019',
            'ext': 'mp4',
            'title': 'Débat des candidats à la Commission européenne',
            'description': 'Débat des candidats à la Commission européenne',
        },
        'params': {
            'skip_download': 'HLS (reqires ffmpeg)'
        },
        'skip': 'Ce direct est terminé et sera disponible en rattrapage dans quelques minutes.',
    }, {
        'url': 'http://www.francetvinfo.fr/economie/entreprises/les-entreprises-familiales-le-secret-de-la-reussite_933271.html',
        'md5': 'f485bda6e185e7d15dbc69b72bae993e',
        'info_dict': {
            'id': 'NI_173343',
            'ext': 'mp4',
            'title': 'Les entreprises familiales : le secret de la réussite',
            'thumbnail': r're:^https?://.*\.jpe?g$',
            'timestamp': 1433273139,
            'upload_date': '20150602',
        },
        'params': {
            # m3u8 downloads
            'skip_download': True,
        },
    }, {
        'url': 'http://france3-regions.francetvinfo.fr/bretagne/cotes-d-armor/thalassa-echappee-breizh-ce-venredi-dans-les-cotes-d-armor-954961.html',
        'md5': 'f485bda6e185e7d15dbc69b72bae993e',
        'info_dict': {
            'id': 'NI_657393',
            'ext': 'mp4',
            'title': 'Olivier Monthus, réalisateur de "Bretagne, le choix de l’Armor"',
            'description': 'md5:a3264114c9d29aeca11ced113c37b16c',
            'thumbnail': r're:^https?://.*\.jpe?g$',
            'timestamp': 1458300695,
            'upload_date': '20160318',
        },
        'params': {
            'skip_download': True,
        },
    }, {
        # Dailymotion embed
        'url': 'http://www.francetvinfo.fr/politique/notre-dame-des-landes/video-sur-france-inter-cecile-duflot-denonce-le-regard-meprisant-de-patrick-cohen_1520091.html',
        'md5': 'ee7f1828f25a648addc90cb2687b1f12',
        'info_dict': {
            'id': 'x4iiko0',
            'ext': 'mp4',
            'title': 'NDDL, référendum, Brexit : Cécile Duflot répond à Patrick Cohen',
            'description': 'Au lendemain de la victoire du "oui" au référendum sur l\'aéroport de Notre-Dame-des-Landes, l\'ancienne ministre écologiste est l\'invitée de Patrick Cohen. Plus d\'info : https://www.franceinter.fr/emissions/le-7-9/le-7-9-27-juin-2016',
            'timestamp': 1467011958,
            'upload_date': '20160627',
            'uploader': 'France Inter',
            'uploader_id': 'x2q2ez',
        },
        'add_ie': ['Dailymotion'],
    }, {
        'url': 'http://france3-regions.francetvinfo.fr/limousin/emissions/jt-1213-limousin',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        page_title = mobj.group('title')
        webpage = self._download_webpage(url, page_title)

        dmcloud_url = DailymotionCloudIE._extract_dmcloud_url(webpage)
        if dmcloud_url:
            return self.url_result(dmcloud_url, DailymotionCloudIE.ie_key())

        dailymotion_urls = DailymotionIE._extract_urls(webpage)
        if dailymotion_urls:
            return self.playlist_result([
                self.url_result(dailymotion_url, DailymotionIE.ie_key())
                for dailymotion_url in dailymotion_urls])

        video_id, catalogue = self._search_regex(
            (r'id-video=([^@]+@[^"]+)',
             r'<a[^>]+href="(?:https?:)?//videos\.francetv\.fr/video/([^@]+@[^"]+)"'),
            webpage, 'video id').split('@')
        return self._extract_video(video_id, catalogue)


class GenerationQuoiIE(InfoExtractor):
    IE_NAME = 'france2.fr:generation-quoi'
    _VALID_URL = r'https?://generation-quoi\.france2\.fr/portrait/(?P<id>[^/?#]+)'

    _TEST = {
        'url': 'http://generation-quoi.france2.fr/portrait/garde-a-vous',
        'info_dict': {
            'id': 'k7FJX8VBcvvLmX4wA5Q',
            'ext': 'mp4',
            'title': 'Génération Quoi - Garde à Vous',
            'uploader': 'Génération Quoi',
        },
        'params': {
            # It uses Dailymotion
            'skip_download': True,
        },
    }

    def _real_extract(self, url):
        display_id = self._match_id(url)
        info_url = compat_urlparse.urljoin(url, '/medias/video/%s.json' % display_id)
        info_json = self._download_webpage(info_url, display_id)
        info = json.loads(info_json)
        return self.url_result('http://www.dailymotion.com/video/%s' % info['id'],
                               ie='Dailymotion')


class CultureboxIE(FranceTVBaseInfoExtractor):
    IE_NAME = 'culturebox.francetvinfo.fr'
    _VALID_URL = r'https?://(?:m\.)?culturebox\.francetvinfo\.fr/(?P<name>.*?)(\?|$)'

    _TEST = {
        'url': 'http://culturebox.francetvinfo.fr/live/musique/musique-classique/le-livre-vermeil-de-montserrat-a-la-cathedrale-delne-214511',
        'md5': '9b88dc156781c4dbebd4c3e066e0b1d6',
        'info_dict': {
            'id': 'EV_50111',
            'ext': 'flv',
            'title': "Le Livre Vermeil de Montserrat à la Cathédrale d'Elne",
            'description': 'md5:f8a4ad202e8fe533e2c493cc12e739d9',
            'upload_date': '20150320',
            'timestamp': 1426892400,
            'duration': 2760.9,
        },
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        name = mobj.group('name')

        webpage = self._download_webpage(url, name)

        if ">Ce live n'est plus disponible en replay<" in webpage:
            raise ExtractorError('Video %s is not available' % name, expected=True)

        video_id, catalogue = self._search_regex(
            r'"http://videos\.francetv\.fr/video/([^@]+@[^"]+)"', webpage, 'video id').split('@')

        return self._extract_video(video_id, catalogue)
