# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor


class CTVIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?(?P<domain>ctv|tsn|bnn|thecomedynetwork)\.ca/.*?(?:\bvid=|-vid|~|%7E)(?P<id>[0-9.]+)'
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
    }, {
        'url': 'http://www.thecomedynetwork.ca/video/player?vid=923582',
        'only_matching': True,
    }, {
        'url': 'http://www.tsn.ca/video/expectations-high-for-milos-raonic-at-us-open~939549',
        'only_matching': True,
    }, {
        'url': 'http://www.bnn.ca/video/berman-s-call-part-two-viewer-questions~939654',
        'only_matching': True,
    }, {
        'url': 'http://www.ctv.ca/YourMorning/Video/S1E6-Monday-August-29-2016-vid938009',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        domain, video_id = re.match(self._VALID_URL, url).groups()
        if domain == 'thecomedynetwork':
            domain = 'comedy'
        return {
            '_type': 'url_transparent',
            'id': video_id,
            'url': '9c9media:%s_web:%s' % (domain, video_id),
            'ie_key': 'NineCNineMedia',
        }
