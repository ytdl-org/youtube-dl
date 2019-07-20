from __future__ import unicode_literals

import random
import re
import string

from .discoverygo import DiscoveryGoBaseIE
from ..compat import (
    compat_str,
    compat_urllib_parse_unquote,
)
from ..utils import (
    ExtractorError,
    try_get,
)
from ..compat import compat_HTTPError


class DiscoveryIE(DiscoveryGoBaseIE):
    _VALID_URL = r'''(?x)https?://
        (?P<site>
            (?:(?:www|go)\.)?discovery|
            (?:www\.)?
                (?:
                    investigationdiscovery|
                    discoverylife|
                    animalplanet|
                    ahctv|
                    destinationamerica|
                    sciencechannel|
                    tlc|
                    velocity
                )|
            watch\.
                (?:
                    hgtv|
                    foodnetwork|
                    travelchannel|
                    diynetwork|
                    cookingchanneltv|
                    motortrend
                )
        )\.com(?P<path>/tv-shows/[^/]+/(?:video|full-episode)s/(?P<id>[^./?#]+))'''
    _TESTS = [{
        'url': 'https://www.discovery.com/tv-shows/cash-cab/videos/dave-foley',
        'info_dict': {
            'id': '5a2d9b4d6b66d17a5026e1fd',
            'ext': 'mp4',
            'title': 'Dave Foley',
            'description': 'md5:4b39bcafccf9167ca42810eb5f28b01f',
            'duration': 608,
        },
        'params': {
            'skip_download': True,  # requires ffmpeg
        }
    }, {
        'url': 'https://www.investigationdiscovery.com/tv-shows/final-vision/full-episodes/final-vision',
        'only_matching': True,
    }, {
        'url': 'https://go.discovery.com/tv-shows/alaskan-bush-people/videos/follow-your-own-road',
        'only_matching': True,
    }]
    _GEO_COUNTRIES = ['US']
    _GEO_BYPASS = False

    def _real_extract(self, url):
        site, path, display_id = re.match(self._VALID_URL, url).groups()
        webpage = self._download_webpage(url, display_id)

        react_data = self._parse_json(self._search_regex(
            r'window\.__reactTransmitPacket\s*=\s*({.+?});',
            webpage, 'react data'), display_id)
        content_blocks = react_data['layout'][path]['contentBlocks']
        video = next(cb for cb in content_blocks if cb.get('type') == 'video')['content']['items'][0]
        video_id = video['id']

        access_token = None
        cookies = self._get_cookies(url)

        # prefer Affiliate Auth Token over Anonymous Auth Token
        auth_storage_cookie = cookies.get('eosAf') or cookies.get('eosAn')
        if auth_storage_cookie and auth_storage_cookie.value:
            auth_storage = self._parse_json(compat_urllib_parse_unquote(
                compat_urllib_parse_unquote(auth_storage_cookie.value)),
                video_id, fatal=False) or {}
            access_token = auth_storage.get('a') or auth_storage.get('access_token')

        if not access_token:
            access_token = self._download_json(
                'https://%s.com/anonymous' % site, display_id, query={
                    'authRel': 'authorization',
                    'client_id': try_get(
                        react_data, lambda x: x['application']['apiClientId'],
                        compat_str) or '3020a40c2356a645b4b4',
                    'nonce': ''.join([random.choice(string.ascii_letters) for _ in range(32)]),
                    'redirectUri': 'https://fusion.ddmcdn.com/app/mercury-sdk/180/redirectHandler.html?https://www.%s.com' % site,
                })['access_token']

        try:
            headers = self.geo_verification_headers()
            headers['Authorization'] = 'Bearer ' + access_token

            stream = self._download_json(
                'https://api.discovery.com/v1/streaming/video/' + video_id,
                display_id, headers=headers)
        except ExtractorError as e:
            if isinstance(e.cause, compat_HTTPError) and e.cause.code in (401, 403):
                e_description = self._parse_json(
                    e.cause.read().decode(), display_id)['description']
                if 'resource not available for country' in e_description:
                    self.raise_geo_restricted(countries=self._GEO_COUNTRIES)
                if 'Authorized Networks' in e_description:
                    raise ExtractorError(
                        'This video is only available via cable service provider subscription that'
                        ' is not currently supported. You may want to use --cookies.', expected=True)
                raise ExtractorError(e_description)
            raise

        return self._extract_video_info(video, stream, display_id)
