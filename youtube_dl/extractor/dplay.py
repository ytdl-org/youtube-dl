# encoding: utf-8
from __future__ import unicode_literals

import time

from .common import InfoExtractor
from ..utils import int_or_none
from ..compat import compat_urlparse

class DPlayIE(InfoExtractor):
    _VALID_URL = r'(?P<domain>http://(?:it|www)\.dplay\.(?:com|dk|se))/[^/]+/(?P<id>[^/?#]+)'

    _TESTS = [
        {
            'url': 'http://it.dplay.com/take-me-out/stagione-1-episodio-25/',
            'info_dict': {
                'id': '1255600',
                'ext': 'mp4',
                'display_id': 'stagione-1-episodio-25',
                'title': 'Episodio 25',
                'duration': 2761,
                'description': "Gabriele Corsi conduce un nuovo provocante e divertente dating show. 30 ragazze single hanno l'opportunità di conoscere un ragazzo e decidere se tenerlo in gioco oppure no accendendo o spegnendo le luci.",
                'season_number': 1,
                'episode_number': 25,
            },
        },
        {
            'url': 'http://www.dplay.se/nugammalt-77-handelser-som-format-sverige/season-1-svensken-lar-sig-njuta-av-livet/',
            'info_dict': {
                'id': '3172',
                'ext': 'mp4',
                'display_id': 'season-1-svensken-lar-sig-njuta-av-livet',
                'title': 'Svensken lär sig njuta av livet',
                'duration': 2650,
                'description': "\"Svensken lär sig njuta av livet\". Införandet av systembolaget, industrisemestern och Skarastadgan. Med hjälp av arkivmaterial, experter och fakta ska händelserna dissekeras, analyseras och dras till sin absoluta underhållningsspets.",
                'season_number': 1,
                'episode_number': 1,
            },
        },
        {
            'url': 'http://www.dplay.dk/mig-og-min-mor/season-6-episode-12/',
            'info_dict': {
                'id': '70816',
                'ext': 'mp4',
                'display_id': 'season-6-episode-12',
                'title': 'Episode 12',
                'duration': 2563,
                'description': " I sæsonafslutningen sker der store ting for mor og datter.\nDagen er endelig kommet for den højgravide Irina - hun skal føde! Men det bliver en lang og sej kamp for Irina, som selvfølgelig har mor Mila med som støtte hele vejen.\nMor Jette og Jessica er igen hjemme i Danmark efter deres store USA-eventyr. Og for at holde fast i den amerikanske ånd, tager pigerne i dag til gospel-undervisning. \nOg så skal Joy og mor Mia under kniven  - de skal nemlig have gjort lårene mindre og ballerne større. \n ",
                'season_number': 6,
                'episode_number': 12,
            },
        }
    ]

    def _real_extract(self, url):
        #this extrator works with it.dplay.com, www.dplay.se and www.dplay.dk
        # so we need to determine the domain to send the requests to
        domain = self._search_regex(self._VALID_URL, url, 'domain')
        display_id = self._match_id(url)
        webpage = self._download_webpage(url, display_id)
        video_id = self._search_regex(
            r'data-video-id="(\d+)"', webpage, 'video id')

        video_url = compat_urlparse.urljoin(domain, 'api/v2/ajax/videos?video_id=')

        info = self._download_json(video_url + video_id,
            video_id)['data'][0]

        # TODO: consider adding support for 'stream_type=hds', it seems to
        # require setting some cookies
        # get url's TLD to determine which cookie and url to use
        domain_tld = domain.split('.')[-1]
        if domain_tld == 'se' or domain_tld == 'dk':
            self._set_cookie(
                'secure.dplay.%s' % domain_tld, 'dsc-geo',
                '{"countryCode":"%s","expiry":%d}' % (domain_tld.upper(), ((time.time() + 20 * 60) * 1000)))

            manifest_url = self._download_json(
                'https://secure.dplay.%s/secure/api/v2/user/authorization/stream/%s?stream_type=hls' % (domain_tld, video_id),
                video_id, 'Getting manifest url for hls stream')['hls']
        else:
            #.it requires no cookies at this point
            manifest_url = info['hls']

        formats = self._extract_m3u8_formats(
            manifest_url, video_id, ext='mp4', entry_protocol='m3u8_native')

        return {
            'id': video_id,
            'display_id': display_id,
            'title': info['title'],
            'formats': formats,
            'duration': int_or_none(info.get('video_metadata_length'), scale=1000),
            'description': info.get('video_metadata_longDescription'),
            'season_number': int_or_none(info.get('season')),
            'episode_number': int_or_none(info.get('episode')),
        }
