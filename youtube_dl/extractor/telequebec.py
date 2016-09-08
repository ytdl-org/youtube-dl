# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import int_or_none


class TeleQuebecIE(InfoExtractor):
    _VALID_URL = r'https?://zonevideo\.telequebec\.tv/media/(?P<id>\d+)'
    _TEST = {
        'url': 'http://zonevideo.telequebec.tv/media/20984/le-couronnement-de-new-york/couronnement-de-new-york',
        'md5': 'fe95a0957e5707b1b01f5013e725c90f',
        'info_dict': {
            'id': '20984',
            'ext': 'mp4',
            'title': 'Le couronnement de New York',
            'description': 'md5:f5b3d27a689ec6c1486132b2d687d432',
            'upload_date': '20160220',
            'timestamp': 1455965438,
        }
    }

    def _real_extract(self, url):
        media_id = self._match_id(url)
        media_data = self._download_json(
            'https://mnmedias.api.telequebec.tv/api/v2/media/' + media_id,
            media_id)['media']
        return {
            '_type': 'url_transparent',
            'id': media_id,
            'url': 'limelight:media:' + media_data['streamInfo']['sourceId'],
            'title': media_data['title'],
            'description': media_data.get('descriptions', [{'text': None}])[0].get('text'),
            'duration': int_or_none(media_data.get('durationInMilliseconds'), 1000),
            'ie_key': 'LimelightMedia',
        }
