# encoding: utf-8

from __future__ import unicode_literals

import re
import json

from .common import InfoExtractor
from ..utils import (
    compat_urlparse,
    ExtractorError,
    clean_html,
    parse_duration,
    compat_urllib_parse_urlparse,
    int_or_none,
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
            if video_url.endswith('.f4m'):
                if georestricted:
                    # See https://github.com/rg3/youtube-dl/issues/3963
                    # m3u8 urls work fine
                    continue
                video_url_parsed = compat_urllib_parse_urlparse(video_url)
                f4m_url = self._download_webpage(
                    'http://hdfauth.francetv.fr/esi/urltokengen2.html?url=%s' % video_url_parsed.path,
                    video_id, 'Downloading f4m manifest token', fatal=False)
                if f4m_url:
                    f4m_formats = self._extract_f4m_formats(f4m_url, video_id)
                    for f4m_format in f4m_formats:
                        f4m_format['preference'] = 1
                    formats.extend(f4m_formats)
            elif video_url.endswith('.m3u8'):
                formats.extend(self._extract_m3u8_formats(video_url, video_id, 'mp4'))
            elif video_url.startswith('rtmp'):
                formats.append({
                    'url': video_url,
                    'format_id': 'rtmp-%s' % format_id,
                    'ext': 'flv',
                    'preference': 1,
                })
            else:
                formats.append({
                    'url': video_url,
                    'format_id': format_id,
                    'preference': -1,
                })
        self._sort_formats(formats)

        return {
            'id': video_id,
            'title': info['titre'],
            'description': clean_html(info['synopsis']),
            'thumbnail': compat_urlparse.urljoin('http://pluzz.francetv.fr', info['image']),
            'duration': parse_duration(info['duree']),
            'timestamp': int_or_none(info['diffusion']['timestamp']),
            'formats': formats,
        }


class PluzzIE(FranceTVBaseInfoExtractor):
    IE_NAME = 'pluzz.francetv.fr'
    _VALID_URL = r'https?://pluzz\.francetv\.fr/videos/(.*?)\.html'

    # Can't use tests, videos expire in 7 days

    def _real_extract(self, url):
        title = re.match(self._VALID_URL, url).group(1)
        webpage = self._download_webpage(url, title)
        video_id = self._search_regex(
            r'data-diffusion="(\d+)"', webpage, 'ID')
        return self._extract_video(video_id, 'Pluzz')


class FranceTvInfoIE(FranceTVBaseInfoExtractor):
    IE_NAME = 'francetvinfo.fr'
    _VALID_URL = r'https?://(?:www|mobile)\.francetvinfo\.fr/.*/(?P<title>.+)\.html'

    _TESTS = [{
        'url': 'http://www.francetvinfo.fr/replay-jt/france-3/soir-3/jt-grand-soir-3-lundi-26-aout-2013_393427.html',
        'info_dict': {
            'id': '84981923',
            'ext': 'flv',
            'title': 'Soir 3',
            'upload_date': '20130826',
            'timestamp': 1377548400,
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
    }]

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        page_title = mobj.group('title')
        webpage = self._download_webpage(url, page_title)
        video_id, catalogue = self._search_regex(
            r'id-video=([^@]+@[^"]+)', webpage, 'video id').split('@')
        return self._extract_video(video_id, catalogue)


class FranceTVIE(FranceTVBaseInfoExtractor):
    IE_NAME = 'francetv'
    IE_DESC = 'France 2, 3, 4, 5 and Ô'
    _VALID_URL = r'''(?x)https?://www\.france[2345o]\.fr/
        (?:
            emissions/.*?/(videos|emissions)/(?P<id>[^/?]+)
        |   (emissions?|jt)/(?P<key>[^/?]+)
        )'''

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
            'url': 'http://www.france5.fr/emissions/c-a-dire/videos/92837968',
            'md5': '78f0f4064f9074438e660785bbf2c5d9',
            'info_dict': {
                'id': '108961659',
                'ext': 'flv',
                'title': 'C à dire ?!',
                'description': 'md5:1a4aeab476eb657bf57c4ff122129f81',
                'upload_date': '20140915',
                'timestamp': 1410795000,
            },
        },
        # franceo
        {
            'url': 'http://www.franceo.fr/jt/info-afrique/04-12-2013',
            'md5': '52f0bfe202848b15915a2f39aaa8981b',
            'info_dict': {
                'id': '108634970',
                'ext': 'flv',
                'title': 'Infô Afrique',
                'description': 'md5:ebf346da789428841bee0fd2a935ea55',
                'upload_date': '20140915',
                'timestamp': 1410822000,
            },
        },
    ]

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        webpage = self._download_webpage(url, mobj.group('key') or mobj.group('id'))
        video_id, catalogue = self._html_search_regex(
            r'href="http://videos\.francetv\.fr/video/([^@]+@[^"]+)"',
            webpage, 'video ID').split('@')
        return self._extract_video(video_id, catalogue)


class GenerationQuoiIE(InfoExtractor):
    IE_NAME = 'france2.fr:generation-quoi'
    _VALID_URL = r'https?://generation-quoi\.france2\.fr/portrait/(?P<name>.*)(\?|$)'

    _TEST = {
        'url': 'http://generation-quoi.france2.fr/portrait/garde-a-vous',
        'file': 'k7FJX8VBcvvLmX4wA5Q.mp4',
        'info_dict': {
            'title': 'Génération Quoi - Garde à Vous',
            'uploader': 'Génération Quoi',
        },
        'params': {
            # It uses Dailymotion
            'skip_download': True,
        },
        'skip': 'Only available from France',
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        name = mobj.group('name')
        info_url = compat_urlparse.urljoin(url, '/medias/video/%s.json' % name)
        info_json = self._download_webpage(info_url, name)
        info = json.loads(info_json)
        return self.url_result('http://www.dailymotion.com/video/%s' % info['id'],
                               ie='Dailymotion')


class CultureboxIE(FranceTVBaseInfoExtractor):
    IE_NAME = 'culturebox.francetvinfo.fr'
    _VALID_URL = r'https?://(?:m\.)?culturebox\.francetvinfo\.fr/(?P<name>.*?)(\?|$)'

    _TEST = {
        'url': 'http://culturebox.francetvinfo.fr/festivals/dans-les-jardins-de-william-christie/dans-les-jardins-de-william-christie-le-camus-162553',
        'md5': '5ad6dec1ffb2a3fbcb20cc4b744be8d6',
        'info_dict': {
            'id': 'EV_22853',
            'ext': 'flv',
            'title': 'Dans les jardins de William Christie - Le Camus',
            'description': 'md5:4710c82315c40f0c865ca8b9a68b5299',
            'upload_date': '20140829',
            'timestamp': 1409317200,
        },
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        name = mobj.group('name')
        webpage = self._download_webpage(url, name)
        video_id, catalogue = self._search_regex(
            r'"http://videos\.francetv\.fr/video/([^@]+@[^"]+)"', webpage, 'video id').split('@')

        return self._extract_video(video_id, catalogue)
