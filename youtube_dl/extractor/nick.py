# coding: utf-8
from __future__ import unicode_literals

from .mtv import MTVServicesInfoExtractor
from ..compat import compat_urllib_parse_urlencode


class NickIE(MTVServicesInfoExtractor):
    IE_NAME = 'nick.com'
    _VALID_URL = r'https?://(?:www\.)?nick\.com/videos/clip/(?P<id>[^/?#.]+)'
    _FEED_URL = 'http://udat.mtvnservices.com/service1/dispatch.htm'
    _TESTS = [{
        'url': 'http://www.nick.com/videos/clip/alvinnn-and-the-chipmunks-112-full-episode.html',
        'playlist': [
            {
                'md5': '6e5adc1e28253bbb1b28ab05403dd4d4',
                'info_dict': {
                    'id': 'be6a17b0-412d-11e5-8ff7-0026b9414f30',
                    'ext': 'mp4',
                    'title': 'ALVINNN!!! and The Chipmunks: "Mojo Missing/Who\'s The Animal" S1',
                    'description': 'Alvin is convinced his mojo was in a cap he gave to a fan, and must find a way to get his hat back before the Chipmunks’ big concert.\nDuring a costume visit to the zoo, Alvin finds himself mistaken for the real Tasmanian devil.',

                }
            },
            {
                'md5': 'd7be441fc53a1d4882fa9508a1e5b3ce',
                'info_dict': {
                    'id': 'be6b8f96-412d-11e5-8ff7-0026b9414f30',
                    'ext': 'mp4',
                    'title': 'ALVINNN!!! and The Chipmunks: "Mojo Missing/Who\'s The Animal" S2',
                    'description': 'Alvin is convinced his mojo was in a cap he gave to a fan, and must find a way to get his hat back before the Chipmunks’ big concert.\nDuring a costume visit to the zoo, Alvin finds himself mistaken for the real Tasmanian devil.',

                }
            },
            {
                'md5': 'efffe1728a234b2b0d2f2b343dd1946f',
                'info_dict': {
                    'id': 'be6cf7e6-412d-11e5-8ff7-0026b9414f30',
                    'ext': 'mp4',
                    'title': 'ALVINNN!!! and The Chipmunks: "Mojo Missing/Who\'s The Animal" S3',
                    'description': 'Alvin is convinced his mojo was in a cap he gave to a fan, and must find a way to get his hat back before the Chipmunks’ big concert.\nDuring a costume visit to the zoo, Alvin finds himself mistaken for the real Tasmanian devil.',
                }
            },
            {
                'md5': '1ec6690733ab9f41709e274a1d5c7556',
                'info_dict': {
                    'id': 'be6e3354-412d-11e5-8ff7-0026b9414f30',
                    'ext': 'mp4',
                    'title': 'ALVINNN!!! and The Chipmunks: "Mojo Missing/Who\'s The Animal" S4',
                    'description': 'Alvin is convinced his mojo was in a cap he gave to a fan, and must find a way to get his hat back before the Chipmunks’ big concert.\nDuring a costume visit to the zoo, Alvin finds himself mistaken for the real Tasmanian devil.',
                }
            },
        ],
    }]

    def _get_feed_query(self, uri):
        return compat_urllib_parse_urlencode({
            'feed': 'nick_arc_player_prime',
            'mgid': uri,
        })

    def _extract_mgid(self, webpage):
        return self._search_regex(r'data-contenturi="([^"]+)', webpage, 'mgid')
