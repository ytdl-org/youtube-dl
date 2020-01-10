# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from .dplay import DPlayIE

from ..utils import (
    urljoin
)


class DiscoveryNetworksDeIE(DPlayIE):
    _VALID_URL = r'https?://(?:www\.)?(?P<domain>(?:tlc|dmax)\.de|dplay\.co\.uk)/(?:programme|show)/(?P<programme>[^/]+)/video/(?P<alternate_id>[^/]+)'

    _TESTS = [{
        'url': 'https://www.tlc.de/programme/breaking-amish/video/die-welt-da-drauen/DCB331270001100',
        'info_dict': {
            'id': '78867',
            'ext': 'mp4',
            'title': 'Die Welt da draußen',
            'description': 'md5:61033c12b73286e409d99a41742ef608',
            'timestamp': 1554069600,
            'upload_date': '20190331',
        },
        'params': {
            'format': 'bestvideo',
            'skip_download': True,
        },
    }, {
        'url': 'https://www.dmax.de/programme/dmax-highlights/video/tuning-star-sidney-hoffmann-exklusiv-bei-dmax/191023082312316',
        'only_matching': True,
    }, {
        'url': 'https://www.dplay.co.uk/show/ghost-adventures/video/hotel-leger-103620/EHD_280313B',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        domain, programme, alternate_id = re.match(self._VALID_URL, url).groups()
        country = 'GB' if domain == 'dplay.co.uk' else 'DE'
        realm = 'questuk' if country == 'GB' else domain.replace('.', '')
        return self._get_disco_api_info(
            url, '%s/%s' % (programme, alternate_id),
            'sonic-eu1-prod.disco-api.com', realm, country)


class DiscoveryNetworksDePlaylistIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?(?P<domain>(?:tlc|dmax)\.de|dplay\.co\.uk)/(?P<type>programme|show)/(?P<programme>[^/]+)'

    _TESTS = [{
        'url': 'https://www.dplay.co.uk/show/hairy-bikers-mississippi-adventure',
        'info_dict': {
            'id': 'hairy-bikers-mississippi-adventure',
            'title': 'Hairy Bikers\' Mississippi Adventure'
        },
        'playlist_mincount': 2
    }, {
        'url': 'https://www.dplay.co.uk/show/diners-drive-ins-and-dives',
        'info_dict': {
            'id': 'diners-drive-ins-and-dives',
            'title': 'Diners, Drive-Ins, And Dives'
        },
        'playlist_mincount': 2
    }, {
        'url': 'https://www.dmax.de/programme/naked-survival',
        'info_dict': {
            'id': 'naked-survival',
            'title': 'Naked Survival'
        },
        'playlist_mincount': 2
    }]

    @classmethod
    def suitable(cls, url):
        return False if DiscoveryNetworksDeIE.suitable(url) else super(
            DiscoveryNetworksDePlaylistIE, cls).suitable(url)

    def _extract_episodes(self, url, webpage, _type, program):
        episodes = []
        for episode in re.finditer(r'"path":"' + program + r'(?P<episode>/.+?)"', webpage):
            episode_url = urljoin(url, '/' + _type + '/' + program + '/video' + episode.group('episode'))
            if episode_url not in episodes:
                episodes.append(episode_url)
        return episodes

    def _real_extract(self, url):
        domain, _type, programme = re.match(self._VALID_URL, url).groups()
        webpage = self._download_webpage(url, programme)

        title = self._html_search_regex(
            r'<div class=".*?show-header__title">(.+?)</div>', webpage,
            'title', default=None)

        if title:
            title = re.sub(r'\s*\|\s*.+?$', '', title)

        episodes = self._extract_episodes(url, webpage, _type, programme)

        entries = [self.url_result(ep, ie=DiscoveryNetworksDeIE.ie_key()) for ep in episodes]

        return self.playlist_result(entries, programme, title)
