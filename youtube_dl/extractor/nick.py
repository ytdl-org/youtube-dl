# coding: utf-8
from __future__ import unicode_literals

import re

from .mtv import MTVServicesInfoExtractor
from ..utils import update_url_query


class NickIE(MTVServicesInfoExtractor):
    # None of videos on the website are still alive?
    IE_NAME = 'nick.com'
    _VALID_URL = r'https?://(?:(?:www|beta)\.)?nick(?:jr)?\.com/(?:[^/]+/)?(?:videos/clip|[^/]+/videos)/(?P<id>[^/?#.]+)'
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
    }, {
        'url': 'http://www.nickjr.com/paw-patrol/videos/pups-save-a-goldrush-s3-ep302-full-episode/',
        'only_matching': True,
    }, {
        'url': 'http://beta.nick.com/nicky-ricky-dicky-and-dawn/videos/nicky-ricky-dicky-dawn-301-full-episode/',
        'only_matching': True,
    }]

    def _get_feed_query(self, uri):
        return {
            'feed': 'nick_arc_player_prime',
            'mgid': uri,
        }

    def _extract_mgid(self, webpage):
        return self._search_regex(r'data-contenturi="([^"]+)', webpage, 'mgid')


class NickDeIE(MTVServicesInfoExtractor):
    IE_NAME = 'nick.de'
    _VALID_URL = r'https?://(?:www\.)?(?P<host>nick\.de|nickelodeon\.(?:nl|at))/(?:playlist|shows)/(?:[^/]+/)*(?P<id>[^/?#&]+)'
    _TESTS = [{
        'url': 'http://www.nick.de/playlist/3773-top-videos/videos/episode/17306-zu-wasser-und-zu-land-rauchende-erdnusse',
        'only_matching': True,
    }, {
        'url': 'http://www.nick.de/shows/342-icarly',
        'only_matching': True,
    }, {
        'url': 'http://www.nickelodeon.nl/shows/474-spongebob/videos/17403-een-kijkje-in-de-keuken-met-sandy-van-binnenuit',
        'only_matching': True,
    }, {
        'url': 'http://www.nickelodeon.at/playlist/3773-top-videos/videos/episode/77993-das-letzte-gefecht',
        'only_matching': True,
    }]

    def _extract_mrss_url(self, webpage, host):
        return update_url_query(self._search_regex(
            r'data-mrss=(["\'])(?P<url>http.+?)\1', webpage, 'mrss url', group='url'),
            {'siteKey': host})

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')
        host = mobj.group('host')

        webpage = self._download_webpage(url, video_id)

        mrss_url = self._extract_mrss_url(webpage, host)

        return self._get_videos_info_from_url(mrss_url, video_id)


class NickNightIE(NickDeIE):
    IE_NAME = 'nicknight'
    _VALID_URL = r'https?://(?:www\.)(?P<host>nicknight\.(?:de|at|tv))/(?:playlist|shows)/(?:[^/]+/)*(?P<id>[^/?#&]+)'
    _TESTS = [{
        'url': 'http://www.nicknight.at/shows/977-awkward/videos/85987-nimmer-beste-freunde',
        'only_matching': True,
    }, {
        'url': 'http://www.nicknight.at/shows/977-awkward',
        'only_matching': True,
    }, {
        'url': 'http://www.nicknight.at/shows/1900-faking-it',
        'only_matching': True,
    }]

    def _extract_mrss_url(self, webpage, *args):
        return self._search_regex(
            r'mrss\s*:\s*(["\'])(?P<url>http.+?)\1', webpage,
            'mrss url', group='url')
