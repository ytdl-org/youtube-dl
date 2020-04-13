# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from .jwplatform import JWPlatformIE


class SpiegelIE(InfoExtractor):
    _UUID_RE = r'[\da-f]{8}-[\da-f]{4}-[\da-f]{4}-[\da-f]{4}-[\da-f]{12}'
    _VALID_URL = r'https?://(?:www\.)?spiegel\.de(?:/[^/]+)+/[^/]*-(?P<id>[0-9]+|%s)(?:-embed|-iframe)?(?:\.html)?(?:#.*)?$' % _UUID_RE
    _TESTS = [{
        'url': 'http://www.spiegel.de/video/vulkan-tungurahua-in-ecuador-ist-wieder-aktiv-video-1259285.html',
        'md5': '50c7948883ec85a3e431a0a44b7ad1d6',
        'info_dict': {
            'id': 'II0BUyxY',
            'display_id': '1259285',
            'ext': 'mp4',
            'title': 'Vulkan Tungurahua in Ecuador ist wieder aktiv - DER SPIEGEL - Wissenschaft',
            'description': 'md5:8029d8310232196eb235d27575a8b9f4',
            'duration': 48.0,
            'upload_date': '20130311',
            'timestamp': 1362997920,
        },
    }, {
        'url': 'http://www.spiegel.de/video/schach-wm-videoanalyse-des-fuenften-spiels-video-1309159.html',
        'md5': '103904ada1044098f20c34b579eb7cd5',
        'info_dict': {
            'id': 'ALIzWLZJ',
            'display_id': '1309159',
            'ext': 'mp4',
            'title': 'Schach-WM: Videoanalyse des fünften Spiels - DER SPIEGEL - Sport',
            'description': 'md5:c2322b65e58f385a820c10fa03b2d088',
            'duration': 983,
            'upload_date': '20131115',
            'timestamp': 1384550242,
        },
    }, {
        'url': 'https://www.spiegel.de/video/eifel-zoo-aufregung-um-ausgebrochene-raubtiere-video-99018031.html',
        'md5': '8089007d406837b8f320fa5a97d22b20',
        'info_dict': {
            'id': 'FMLessGS',
            'display_id': '99018031',
            'ext': 'mp4',
            'title': 'Eifel-Zoo: Aufregung um ausgebrochene Raubtiere - DER SPIEGEL - Panorama',
            'description': 'md5:7d7a7d9066526203c001bad6ca84c4bf',
            'duration': 112.0,
            'timestamp': 1527874810,
            'upload_date': '20180601',
        },
    }, {
        'url': 'https://www.spiegel.de/panorama/urteile-im-goldmuenzenprozess-haftstrafen-fuer-clanmitglieder-a-aae8df48-43c1-4c61-867d-23f0a2d254b7',
        'md5': '41eeb224bf869e90606bb7d68f5bdd21',
        'info_dict': {
            'id': 'RM8hNagK',
            'display_id': 'aae8df48-43c1-4c61-867d-23f0a2d254b7',
            'ext': 'mp4',
            'title': 'Haftstrafen für Clanmitglieder: SPIEGEL TV über Urteile im Goldmünzenprozess - DER SPIEGEL - Panorama',
            'description': 'md5:eb1ead19809f8cca2e35c22077e2f792',
            'timestamp': 1582618271,
            'upload_date': '20200225'
        },
    }, {
        'url': 'http://www.spiegel.de/video/spiegel-tv-magazin-ueber-guellekrise-in-schleswig-holstein-video-99012776.html',
        'only_matching': True,
    }, {
        'url': 'http://www.spiegel.de/sport/sonst/badminton-wm-die-randsportart-soll-populaerer-werden-a-987092.html',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)
        media_id = self._html_search_regex(r'&#34;mediaId&#34;:&#34;(\w+)&#34;', webpage, "media id")
        return {
            '_type': 'url_transparent',
            'id': video_id,
            'display_id': video_id,
            'url': 'jwplatform:%s' % media_id,
            'title': self._og_search_title(webpage),
            'ie_key': JWPlatformIE.ie_key(),
        }
