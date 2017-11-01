# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..compat import compat_str
from ..utils import (
    int_or_none,
    smuggle_url,
    try_get,
)


class TeleQuebecIE(InfoExtractor):
    _VALID_URL = r'https?://zonevideo\.telequebec\.tv/media/(?P<id>\d+)'
    _TESTS = [{
        'url': 'http://zonevideo.telequebec.tv/media/20984/le-couronnement-de-new-york/couronnement-de-new-york',
        'md5': 'fe95a0957e5707b1b01f5013e725c90f',
        'info_dict': {
            'id': '20984',
            'ext': 'mp4',
            'title': 'Le couronnement de New York',
            'description': 'md5:f5b3d27a689ec6c1486132b2d687d432',
            'upload_date': '20170201',
            'timestamp': 1485972222,
        }
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
        return {
            '_type': 'url_transparent',
            'id': media_id,
            'url': smuggle_url(
                'limelight:media:' + media_data['streamInfo']['sourceId'],
                {'geo_countries': ['CA']}),
            'title': media_data['title'],
            'description': try_get(
                media_data, lambda x: x['descriptions'][0]['text'], compat_str),
            'duration': int_or_none(
                media_data.get('durationInMilliseconds'), 1000),
            'ie_key': 'LimelightMedia',
        }

class TeleQuebecEmissionsIE(InfoExtractor):
    _VALID_URL = r'https?://[^.\s]+\.telequebec\.tv/emissions/(?P<id>[^/]+)'
    _TEST = {
        'url': 'http://lindicemcsween.telequebec.tv/emissions/100430013/des-soins-esthetiques-a-377-d-interets-annuels-ca-vous-tente',
        'info_dict': {
            'id': '66648a6aef914fe3badda25e81a4d50a',
            'ext': 'mp4',
            'title': 'Des soins esth\u00e9tiques \u00e0 377 % d\'int\u00e9r\u00eats annuels, \u00e7a vous tente?',
            'description': 'Certains plans de financement peuvent assassiner votre portefeuille! D\u00e9monstration avec des soins esth\u00e9tiques. Louis T. aime le confort financier, mais n\'a pas h\u00e9sit\u00e9 \u00e0 laisser tomber la s\u00e9curit\u00e9 d\'emploi pour faire ce qu\'il aime le plus au monde. Les gens qui font de l\'argent au noir sont plus riches que les autres, mais ils appauvrissent notre soci\u00e9t\u00e9 et Pierre-Yves rencontre Diane Ch\u00eanevert, qui a utilis\u00e9 toutes ses \u00e9conomies pour fonder un centre d\'aide pour les enfants handicap\u00e9s.',
            'upload_date': '20171024',
            'timestamp': 1508862118,
        },
        'params': {
            # m3u8 download
            'skip_download': True,
        },
    }

    def _real_extract(self, url):
        display_id = self._match_id(url)
        webpage = self._download_webpage(url,display_id)
        mediauid = self._search_regex(r'mediaUID:[\s]?["\']Limelight_(?P<mediauid>\w+)["\']',webpage,'mediaUID')
        return {
            '_type': 'url_transparent',
            'id': mediauid,
            'url': smuggle_url(
                'limelight:media:' + mediauid,
                {'geo_countries': ['CA']}),
            'title': self._og_search_title(webpage),
            'description': self._og_search_description(webpage),
            'ie_key': 'LimelightMedia',
        }
