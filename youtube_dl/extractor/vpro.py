# coding: utf-8
from __future__ import unicode_literals

import base64
import datetime
import hashlib
import hmac
import re

from .common import InfoExtractor
from ..utils import (
    strip_or_none,
    get_element_by_class,
)

class Vpro3Voor12IE(InfoExtractor):
    _VALID_URL = r'https://3voor12.vpro.nl/speel~(?P<id>\w+)~'
    _TEST = {
        'url': 'https://3voor12.vpro.nl/speel~WO_VPRO_575949~the-veils-live-op-down-the-rabbit-hole-2014~.html',
        'md5': '5514d8703a03e6443f0aa8f2e6400810',
        'info_dict': {
            'id': 'WO_VPRO_575949',
            'ext': 'mp4',
            'title': 'The Veils live op Down The Rabbit Hole 2014',
        }
    }

    def _get_server_config(self, content):
        return dict(
            re.findall(
                r'(apiKey|apiSecret|locationApiKey|locationApiSecret|vpronlApiKey|vpronlSecret): "(\w+)"',
                content,
                re.MULTILINE,
            )
        )

    def _get_credentials(self, vpronl_secret, x_npo_date, x_npo_mid=None, x_npo_url=None):
        msg = 'origin:https://3voor12.vpro.nl'
        if x_npo_date:
            msg += ',x-npo-date:' + x_npo_date
        if x_npo_url:
            msg += ',x-npo-url:' + x_npo_url
        if x_npo_mid:
            msg += ',uri:/v1/api/media/%s' % x_npo_mid
        a = hmac.new(vpronl_secret.encode(), msg.encode(), hashlib.sha256)
        return base64.b64encode(a.digest()).decode('utf-8')

    def _get_authorization(self, api_key, api_secret, x_npo_date, x_npo_mid=None, x_npo_url=None):
        return 'NPO %s:%s' % (api_key, self._get_credentials(api_secret, x_npo_date, x_npo_mid, x_npo_url))

    def _get_media(self, html_url, vpronl_api_key, vpronl_secret, x_npo_date, x_npo_mid):
        headers = {
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Authorization': self._get_authorization(
                vpronl_api_key, vpronl_secret, x_npo_date, x_npo_mid
            ),
            'Origin': 'https://3voor12.vpro.nl',
            'Referer': html_url,
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/12.0 Safari/605.1.15',
            'x-npo-date': x_npo_date,
        }

        return self._download_json(
            'https://rs.poms.omroep.nl/v1/api/media/%s' % x_npo_mid,
            note='Downloading JSON media metadata',
            video_id=x_npo_mid,
            headers=headers,
        )

    def _get_protected_location(self, html_url, video_id, api_key, api_secret, x_npo_date, x_npo_url):
        headers = {
            'Content-Type': 'text/plain',
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Authorization': self._get_authorization(
                api_key, api_secret, x_npo_date, x_npo_url=x_npo_url
            ),
            'Origin': 'https://3voor12.vpro.nl',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/12.0 Safari/605.1.15',
            'Referer': html_url,
            'x-npo-date': x_npo_date,
            'x-npo-url': x_npo_url,
        }

        data = x_npo_url.encode()

        response = self._download_json(
            'https://rs.vpro.nl/v3/api/locations?plainText=true',
            video_id,
            note='Downloading JSON media location metadata',
            headers=headers,
            data=data,
        )
        return response['programUrl']

    def _get_mp4_location(self, locations):
        for loc in locations:
            try:
                if loc['avAttributes']['avFileFormat'] == 'MP4':
                    return loc['programUrl']
            except KeyError:
                raise

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)
        server_config = self._get_server_config(webpage)
        x_npo_date = datetime.datetime.now().strftime('%a, %d %b %Y %H:%M:%S GMT')

        locations = self._get_media(
            url,
            vpronl_api_key=server_config['vpronlApiKey'],
            vpronl_secret=server_config['vpronlSecret'],
            x_npo_date=x_npo_date,
            x_npo_mid=video_id,
        )['locations']

        mp4_url = self._get_mp4_location(locations)

        protected_url = self._get_protected_location(
            url,
            video_id,
            api_key=server_config['locationApiKey'],
            api_secret=server_config['locationApiSecret'],
            x_npo_date=x_npo_date,
            x_npo_url=mp4_url,
        )

        return {
            'id': video_id,
            'title': (self._og_search_title(webpage) or
                      strip_or_none(get_element_by_class('media-platform-subtitle', webpage))),
            'url': protected_url,
        }
