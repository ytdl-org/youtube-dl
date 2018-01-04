from __future__ import unicode_literals

import random
import re
import string

from .discoverygo import DiscoveryGoBaseIE
from ..utils import (
    ExtractorError,
    update_url_query,
)
from ..compat import compat_HTTPError


class DiscoveryIE(DiscoveryGoBaseIE):
    _VALID_URL = r'''(?x)https?://(?:www\.)?(?:
            discovery|
            investigationdiscovery|
            discoverylife|
            animalplanet|
            ahctv|
            destinationamerica|
            sciencechannel|
            tlc|
            velocity
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
    }]
    _GEO_COUNTRIES = ['US']
    _GEO_BYPASS = False

    def _real_extract(self, url):
        path, display_id = re.match(self._VALID_URL, url).groups()
        webpage = self._download_webpage(url, display_id)

        react_data = self._parse_json(self._search_regex(
            r'window\.__reactTransmitPacket\s*=\s*({.+?});',
            webpage, 'react data'), display_id)
        content_blocks = react_data['layout'][path]['contentBlocks']
        video = next(cb for cb in content_blocks if cb.get('type') == 'video')['content']['items'][0]
        video_id = video['id']

        access_token = self._download_json(
            'https://www.discovery.com/anonymous', display_id, query={
                'authLink': update_url_query(
                    'https://login.discovery.com/v1/oauth2/authorize', {
                        'client_id': react_data['application']['apiClientId'],
                        'redirect_uri': 'https://fusion.ddmcdn.com/app/mercury-sdk/180/redirectHandler.html',
                        'response_type': 'anonymous',
                        'state': 'nonce,' + ''.join([random.choice(string.ascii_letters) for _ in range(32)]),
                    })
            })['access_token']

        try:
            stream = self._download_json(
                'https://api.discovery.com/v1/streaming/video/' + video_id,
                display_id, headers={
                    'Authorization': 'Bearer ' + access_token,
                })
        except ExtractorError as e:
            if isinstance(e.cause, compat_HTTPError) and e.cause.code == 403:
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
