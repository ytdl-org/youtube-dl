# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor


class CTVIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?ctv\.ca/video/player\?vid=(?P<id>[0-9.]+)'
    _TESTS = [{
        'url': 'http://www.ctv.ca/video/player?vid=706966',
        'md5': 'ff2ebbeae0aa2dcc32a830c3fd69b7b0',
        'info_dict': {
            'id': '706966',
            'ext': 'mp4',
            'title': 'Larry Day and Richard Jutras on the TIFF red carpet of \'Stonewall\'',
            'description': 'etalk catches up with Larry Day and Richard Jutras on the TIFF red carpet of "Stonewall”.',
            'upload_date': '20150919',
            'timestamp': 1442624700,
        },
        'expected_warnings': ['HTTP Error 404'],
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        return {
            '_type': 'url_transparent',
            'id': video_id,
            'url': '9c9media:ctv_web:%s' % video_id,
            'ie_key': 'NineCNineMedia',
        }
