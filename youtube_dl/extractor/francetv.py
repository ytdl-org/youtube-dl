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
    def _extract_video(self, video_id, catalogue):
        info = self._download_json(
            'http://webservices.francetelevisions.fr/tools/getInfosOeuvre/v2/?idDiffusion=%s&catalogue=%s'
            % (video_id, catalogue),
            video_id, 'Downloading video JSON')

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


class PluzzIE(FranceTVBaseInfoExtractor):
    IE_NAME = 'pluzz.francetv.fr'
    _VALID_URL = r'https?://(?:m\.)?pluzz\.francetv\.fr/videos/(?P<id>.+?)\.html'

    # Can't use tests, videos expire in 7 days

    def _real_extract(self, url):
        display_id = self._match_id(url)

        webpage = self._download_webpage(url, display_id)

        video_id = self._html_search_meta(
            'id_video', webpage, 'video id', default=None)
        if not video_id:
            video_id = self._search_regex(
                r'data-diffusion=["\'](\d+)', webpage, 'video id')

        return self._extract_video(video_id, 'Pluzz')


class FranceTvInfoIE(FranceTVBaseInfoExtractor):
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


class FranceTVIE(FranceTVBaseInfoExtractor):
    IE_NAME = 'francetv'
    IE_DESC = 'France 2, 3, 4, 5 and Ô'
    _VALID_URL = r'''(?x)
                    https?://
                        (?:
                            (?:www\.)?france[2345o]\.fr/
                                (?:
                                    emissions/[^/]+/(?:videos|diffusions)|
                                    emission/[^/]+|
                                    videos|
                                    jt
                                )
                            /|
                            embed\.francetv\.fr/\?ue=
                        )
                        (?P<id>[^/?]+)
                    '''

    _TESTS = [
        # france2
        {
            'url': 'http://www.france2.fr/emissions/13h15-le-samedi-le-dimanche/videos/75540104',
            'md5': 'c03fc87cb85429ffd55df32b9fc05523',
            'info_dict': {
                'id': '109169362',
                'ext': 'flv',
                'title': '13h15, le dimanche...',
                'description': 'md5:9a0932bb465f22d377a449be9d1a0ff7',
                'upload_date': '20140914',
                'timestamp': 1410693600,
            },
        },
        # france3
        {
            'url': 'http://www.france3.fr/emissions/pieces-a-conviction/diffusions/13-11-2013_145575',
            'md5': '679bb8f8921f8623bd658fa2f8364da0',
            'info_dict': {
                'id': '000702326_CAPP_PicesconvictionExtrait313022013_120220131722_Au',
                'ext': 'mp4',
                'title': 'Le scandale du prix des médicaments',
                'description': 'md5:1384089fbee2f04fc6c9de025ee2e9ce',
                'upload_date': '20131113',
                'timestamp': 1384380000,
            },
        },
        # france4
        {
            'url': 'http://www.france4.fr/emissions/hero-corp/videos/rhozet_herocorp_bonus_1_20131106_1923_06112013172108_F4',
            'md5': 'a182bf8d2c43d88d46ec48fbdd260c1c',
            'info_dict': {
                'id': 'rhozet_herocorp_bonus_1_20131106_1923_06112013172108_F4',
                'ext': 'mp4',
                'title': 'Hero Corp Making of - Extrait 1',
                'description': 'md5:c87d54871b1790679aec1197e73d650a',
                'upload_date': '20131106',
                'timestamp': 1383766500,
            },
        },
        # france5
        {
            'url': 'http://www.france5.fr/emissions/c-a-dire/videos/quels_sont_les_enjeux_de_cette_rentree_politique__31-08-2015_908948?onglet=tous&page=1',
            'md5': 'f6c577df3806e26471b3d21631241fd0',
            'info_dict': {
                'id': '123327454',
                'ext': 'flv',
                'title': 'C à dire ?! - Quels sont les enjeux de cette rentrée politique ?',
                'description': 'md5:4a0d5cb5dce89d353522a84462bae5a4',
                'upload_date': '20150831',
                'timestamp': 1441035120,
            },
        },
        # franceo
        {
            'url': 'http://www.franceo.fr/jt/info-soir/18-07-2015',
            'md5': '47d5816d3b24351cdce512ad7ab31da8',
            'info_dict': {
                'id': '125377621',
                'ext': 'flv',
                'title': 'Infô soir',
                'description': 'md5:01b8c6915a3d93d8bbbd692651714309',
                'upload_date': '20150718',
                'timestamp': 1437241200,
                'duration': 414,
            },
        },
        {
            # francetv embed
            'url': 'http://embed.francetv.fr/?ue=8d7d3da1e3047c42ade5a5d7dfd3fc87',
            'info_dict': {
                'id': 'EV_30231',
                'ext': 'flv',
                'title': 'Alcaline, le concert avec Calogero',
                'description': 'md5:61f08036dcc8f47e9cfc33aed08ffaff',
                'upload_date': '20150226',
                'timestamp': 1424989860,
                'duration': 5400,
            },
        },
        {
            'url': 'http://www.france4.fr/emission/highlander/diffusion-du-17-07-2015-04h05',
            'only_matching': True,
        },
        {
            'url': 'http://www.franceo.fr/videos/125377617',
            'only_matching': True,
        }
    ]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)
        video_id, catalogue = self._html_search_regex(
            r'(?:href=|player\.setVideo\(\s*)"http://videos?\.francetv\.fr/video/([^@]+@[^"]+)"',
            webpage, 'video ID').split('@')
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
