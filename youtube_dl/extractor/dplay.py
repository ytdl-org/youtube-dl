# coding: utf-8
from __future__ import unicode_literals

import json
import re
import time

from .common import InfoExtractor
from ..utils import int_or_none


class DPlayIE(InfoExtractor):
    _VALID_URL = r'http://(?P<domain>it\.dplay\.com|www\.dplay\.(?:dk|se|no))/[^/]+/(?P<id>[^/?#]+)'

    _TESTS = [{
        'url': 'http://it.dplay.com/take-me-out/stagione-1-episodio-25/',
        'info_dict': {
            'id': '1255600',
            'display_id': 'stagione-1-episodio-25',
            'ext': 'mp4',
            'title': 'Episodio 25',
            'description': 'md5:cae5f40ad988811b197d2d27a53227eb',
            'duration': 2761,
            'timestamp': 1454701800,
            'upload_date': '20160205',
            'creator': 'RTIT',
            'series': 'Take me out',
            'season_number': 1,
            'episode_number': 25,
            'age_limit': 0,
        },
        'expected_warnings': ['Unable to download f4m manifest'],
    }, {
        'url': 'http://www.dplay.se/nugammalt-77-handelser-som-format-sverige/season-1-svensken-lar-sig-njuta-av-livet/',
        'info_dict': {
            'id': '3172',
            'display_id': 'season-1-svensken-lar-sig-njuta-av-livet',
            'ext': 'flv',
            'title': 'Svensken lär sig njuta av livet',
            'description': 'md5:d3819c9bccffd0fe458ca42451dd50d8',
            'duration': 2650,
            'timestamp': 1365454320,
            'upload_date': '20130408',
            'creator': 'Kanal 5 (Home)',
            'series': 'Nugammalt - 77 händelser som format Sverige',
            'season_number': 1,
            'episode_number': 1,
            'age_limit': 0,
        },
    }, {
        'url': 'http://www.dplay.dk/mig-og-min-mor/season-6-episode-12/',
        'info_dict': {
            'id': '70816',
            'display_id': 'season-6-episode-12',
            'ext': 'flv',
            'title': 'Episode 12',
            'description': 'md5:9c86e51a93f8a4401fc9641ef9894c90',
            'duration': 2563,
            'timestamp': 1429696800,
            'upload_date': '20150422',
            'creator': 'Kanal 4',
            'series': 'Mig og min mor',
            'season_number': 6,
            'episode_number': 12,
            'age_limit': 0,
        },
    }, {
        'url': 'http://www.dplay.no/pga-tour/season-1-hoydepunkter-18-21-februar/',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        display_id = mobj.group('id')
        domain = mobj.group('domain')

        webpage = self._download_webpage(url, display_id)

        video_id = self._search_regex(
            r'data-video-id=["\'](\d+)', webpage, 'video id')

        info = self._download_json(
            'http://%s/api/v2/ajax/videos?video_id=%s' % (domain, video_id),
            video_id)['data'][0]

        title = info['title']

        PROTOCOLS = ('hls', 'hds')
        formats = []

        def extract_formats(protocol, manifest_url):
            if protocol == 'hls':
                formats.extend(self._extract_m3u8_formats(
                    manifest_url, video_id, ext='mp4',
                    entry_protocol='m3u8_native', m3u8_id=protocol, fatal=False))
            elif protocol == 'hds':
                formats.extend(self._extract_f4m_formats(
                    manifest_url + '&hdcore=3.8.0&plugin=flowplayer-3.8.0.0',
                    video_id, f4m_id=protocol, fatal=False))

        domain_tld = domain.split('.')[-1]
        if domain_tld in ('se', 'dk'):
            for protocol in PROTOCOLS:
                self._set_cookie(
                    'secure.dplay.%s' % domain_tld, 'dsc-geo',
                    json.dumps({
                        'countryCode': domain_tld.upper(),
                        'expiry': (time.time() + 20 * 60) * 1000,
                    }))
                stream = self._download_json(
                    'https://secure.dplay.%s/secure/api/v2/user/authorization/stream/%s?stream_type=%s'
                    % (domain_tld, video_id, protocol), video_id,
                    'Downloading %s stream JSON' % protocol, fatal=False)
                if stream and stream.get(protocol):
                    extract_formats(protocol, stream[protocol])
        else:
            for protocol in PROTOCOLS:
                if info.get(protocol):
                    extract_formats(protocol, info[protocol])

        return {
            'id': video_id,
            'display_id': display_id,
            'title': title,
            'description': info.get('video_metadata_longDescription'),
            'duration': int_or_none(info.get('video_metadata_length'), scale=1000),
            'timestamp': int_or_none(info.get('video_publish_date')),
            'creator': info.get('video_metadata_homeChannel'),
            'series': info.get('video_metadata_show'),
            'season_number': int_or_none(info.get('season')),
            'episode_number': int_or_none(info.get('episode')),
            'age_limit': int_or_none(info.get('minimum_age')),
            'formats': formats,
        }
