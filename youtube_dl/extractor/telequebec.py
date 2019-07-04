# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..compat import compat_str
from ..utils import (
    int_or_none,
    smuggle_url,
    try_get,
)


class TeleQuebecBaseIE(InfoExtractor):
    @staticmethod
    def _limelight_result(media_id):
        return {
            '_type': 'url_transparent',
            'url': smuggle_url(
                'limelight:media:' + media_id, {'geo_countries': ['CA']}),
            'ie_key': 'LimelightMedia',
        }


class TeleQuebecIE(TeleQuebecBaseIE):
    _VALID_URL = r'https?://zonevideo\.telequebec\.tv/media/(?P<id>\d+)'
    _TESTS = [{
        # available till 01.01.2023
        'url': 'http://zonevideo.telequebec.tv/media/37578/un-petit-choc-et-puis-repart/un-chef-a-la-cabane',
        'info_dict': {
            'id': '577116881b4b439084e6b1cf4ef8b1b3',
            'ext': 'mp4',
            'title': 'Un petit choc et puis repart!',
            'description': 'md5:b04a7e6b3f74e32d7b294cffe8658374',
            'upload_date': '20180222',
            'timestamp': 1519326631,
        },
        'params': {
            'skip_download': True,
        },
    }, {
        # no description
        'url': 'http://zonevideo.telequebec.tv/media/30261',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        media_id = self._match_id(url)

        media_data = self._download_json(
            'https://mnmedias.api.telequebec.tv/api/v2/media/' + media_id,
            media_id)['media']

        info = self._limelight_result(media_data['streamInfo']['sourceId'])
        info.update({
            'title': media_data.get('title'),
            'description': try_get(
                media_data, lambda x: x['descriptions'][0]['text'], compat_str),
            'duration': int_or_none(
                media_data.get('durationInMilliseconds'), 1000),
        })
        return info


class TeleQuebecEmissionIE(TeleQuebecBaseIE):
    _VALID_URL = r'''(?x)
                    https?://
                        (?:
                            [^/]+\.telequebec\.tv/emissions/|
                            (?:www\.)?telequebec\.tv/
                        )
                        (?P<id>[^?#&]+)
                    '''
    _TESTS = [{
        'url': 'http://lindicemcsween.telequebec.tv/emissions/100430013/des-soins-esthetiques-a-377-d-interets-annuels-ca-vous-tente',
        'info_dict': {
            'id': '66648a6aef914fe3badda25e81a4d50a',
            'ext': 'mp4',
            'title': "Des soins esthétiques à 377 % d'intérêts annuels, ça vous tente?",
            'description': 'md5:369e0d55d0083f1fc9b71ffb640ea014',
            'upload_date': '20171024',
            'timestamp': 1508862118,
        },
        'params': {
            'skip_download': True,
        },
    }, {
        'url': 'http://bancpublic.telequebec.tv/emissions/emission-49/31986/jeunes-meres-sous-pression',
        'only_matching': True,
    }, {
        'url': 'http://www.telequebec.tv/masha-et-michka/epi059masha-et-michka-3-053-078',
        'only_matching': True,
    }, {
        'url': 'http://www.telequebec.tv/documentaire/bebes-sur-mesure/',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        display_id = self._match_id(url)

        webpage = self._download_webpage(url, display_id)

        media_id = self._search_regex(
            r'mediaUID\s*:\s*["\'][Ll]imelight_(?P<id>[a-z0-9]{32})', webpage,
            'limelight id')

        info = self._limelight_result(media_id)
        info.update({
            'title': self._og_search_title(webpage, default=None),
            'description': self._og_search_description(webpage, default=None),
        })
        return info


class TeleQuebecLiveIE(InfoExtractor):
    _VALID_URL = r'https?://zonevideo\.telequebec\.tv/(?P<id>endirect)'
    _TEST = {
        'url': 'http://zonevideo.telequebec.tv/endirect/',
        'info_dict': {
            'id': 'endirect',
            'ext': 'mp4',
            'title': 're:^Télé-Québec - En direct [0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}$',
            'is_live': True,
        },
        'params': {
            'skip_download': True,
        },
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)

        m3u8_url = None
        webpage = self._download_webpage(
            'https://player.telequebec.tv/Tq_VideoPlayer.js', video_id,
            fatal=False)
        if webpage:
            m3u8_url = self._search_regex(
                r'm3U8Url\s*:\s*(["\'])(?P<url>(?:(?!\1).)+)\1', webpage,
                'm3u8 url', default=None, group='url')
        if not m3u8_url:
            m3u8_url = 'https://teleqmmd.mmdlive.lldns.net/teleqmmd/f386e3b206814e1f8c8c1c71c0f8e748/manifest.m3u8'
        formats = self._extract_m3u8_formats(
            m3u8_url, video_id, 'mp4', m3u8_id='hls')
        self._sort_formats(formats)

        return {
            'id': video_id,
            'title': self._live_title('Télé-Québec - En direct'),
            'is_live': True,
            'formats': formats,
        }
