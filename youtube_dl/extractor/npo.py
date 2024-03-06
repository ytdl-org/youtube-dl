# coding: utf-8
from __future__ import unicode_literals

import json
import re

from .common import InfoExtractor
from ..utils import ExtractorError


class NPOIE(InfoExtractor):
    IE_NAME = 'npo'
    IE_DESC = 'npo.nl'
    _VALID_URL = r'''(?x)
                    (?:
                        https?://
                            (?:www\.)?
                            (?:
                                npo\.nl/(?:[^/]+/)*
                            )
                        )
                        (?P<id>[^/?#]+)
                '''

    _TESTS = [{
        'url': 'https://npo.nl/start/serie/zembla/seizoen-2015/wie-is-de-mol-2/',
        # TODO fill in other test attributes
    }, {
        'url': 'https://npo.nl/start/serie/vpro-tegenlicht/seizoen-11/zwart-geld-de-toekomst-komt-uit-afrika',
        'md5': 'f8065e4e5a7824068ed3c7e783178f2c',
        'info_dict': {
            'id': 'VPWON_1169289',
            'ext': 'm4v',
            'title': 'Tegenlicht: Zwart geld. De toekomst komt uit Afrika',
            'description': 'md5:52cf4eefbc96fffcbdc06d024147abea',
            'upload_date': '20130225',
            'duration': 3000,
        },
    }]

    def _get_token(self, video_id):
        return self._download_json(
            'https://npo.nl/start/api/domain/player-token?productId=%s' % video_id,
            video_id,
            note='Downloading token')['token']

    def _real_extract(self, url):
        # You might want to use removesuffix here,
        # but removesuffix is introduced in Python 3.9
        # and youtube-dl supports Python 3.2+
        if url.endswith('/afspelen'):
            url = url[:-9]
        elif url.endswith('/afspelen/'):
            url = url[:-10]
        url = url.rstrip('/')
        slug = url.split('/')[-1]

        program_metadata = self._download_json('https://npo.nl/start/api/domain/program-detail',
                                               slug,
                                               query={'slug': slug})
        product_id = program_metadata.get('productId')
        images = program_metadata.get('images')
        thumbnail = None
        for image in images:
            thumbnail = image.get('url')
            break
        title = program_metadata.get('title')
        descriptions = program_metadata.get('description', {})
        description = descriptions.get('long') or descriptions.get('short') or descriptions.get('brief')
        duration = program_metadata.get('durationInSeconds')

        if not product_id:
            raise ExtractorError('No productId found for slug: %s' % slug)

        formats = self._download_by_product_id(product_id, slug, url)

        return {
            'id': slug,
            'formats': formats,
            'title': title or slug,
            'description': description or title or slug,
            'thumbnail': thumbnail,
            'duration': duration,
        }

    def _download_by_product_id(self, product_id, slug, url=None):
        token = self._get_token(product_id)
        formats = []
        for profile in (
            'dash',
            # 'hls' is available too, but implementing it doesn't add much
            # As far as I know 'dash' is always available
        ):
            stream_link = self._download_json(
                'https://prod.npoplayer.nl/stream-link', video_id=slug,
                data=json.dumps({
                    'profileName': profile,
                    'drmType': 'widevine',
                    'referrerUrl': url or '',
                }).encode('utf8'),
                headers={
                    'Authorization': token,
                    'Content-Type': 'application/json',
                }
            )
            stream_url = stream_link.get('stream', {}).get('streamURL')
            formats.extend(self._extract_mpd_formats(stream_url, slug, mpd_id='dash', fatal=False))
        return formats


class BNNVaraIE(NPOIE):
    IE_NAME = 'bnnvara'
    IE_DESC = 'bnnvara.nl'
    _VALID_URL = r'https?://(?:www\.)?bnnvara\.nl/videos/[0-9]*'
    _TESTS = [{
        'url': 'https://www.bnnvara.nl/videos/27455',
        # TODO fill in other test attributes
    }]

    def _real_extract(self, url):
        url = url.rstrip('/')
        video_id = url.split('/')[-1]

        media = self._download_json('https://api.bnnvara.nl/bff/graphql',
                                    video_id,
                                    data=json.dumps(
                                        {
                                            'operationName': 'getMedia',
                                            'variables': {
                                                'id': video_id,
                                                'hasAdConsent': False,
                                                'atInternetId': 70
                                            },
                                            'query': 'query getMedia($id: ID!, $mediaUrl: String, $hasAdConsent: Boolean!, $atInternetId: Int) {\n  player(\n    id: $id\n    mediaUrl: $mediaUrl\n    hasAdConsent: $hasAdConsent\n    atInternetId: $atInternetId\n  ) {\n    ... on PlayerSucces {\n      brand {\n        name\n        slug\n        broadcastsEnabled\n        __typename\n      }\n      title\n      programTitle\n      pomsProductId\n      broadcasters {\n        name\n        __typename\n      }\n      duration\n      classifications {\n        title\n        imageUrl\n        type\n        __typename\n      }\n      image {\n        title\n        url\n        __typename\n      }\n      cta {\n        title\n        url\n        __typename\n      }\n      genres {\n        name\n        __typename\n      }\n      subtitles {\n        url\n        language\n        __typename\n      }\n      sources {\n        name\n        url\n        ratio\n        __typename\n      }\n      type\n      token\n      __typename\n    }\n    ... on PlayerError {\n      error\n      __typename\n    }\n    __typename\n  }\n}'
                                        }).encode('utf8'),
                                    headers={
                                        'Content-Type': 'application/json',
                                    })
        product_id = media.get('data', {}).get('player', {}).get('pomsProductId')

        formats = self._download_by_product_id(product_id, video_id)

        return {
            'id': product_id,
            'title': media.get('data', {}).get('player', {}).get('title'),
            'formats': formats,
            'thumbnail': media.get('data', {}).get('player', {}).get('image').get('url'),
        }


class ONIE(NPOIE):
    IE_NAME = 'on'
    IE_DESC = 'ongehoordnederland.tv'
    _VALID_URL = r'https?://(?:www\.)?ongehoordnederland.tv/.*'
    _TESTS = [{
        'url': 'https://ongehoordnederland.tv/2024/03/01/korte-clips/heeft-preppen-zin-betwijfel-dat-je-daar-echt-iets-aan-zult-hebben-bij-oorlog-lydia-daniel/',
        # TODO fill in other test attributes
    }]

    def _real_extract(self, url):
        video_id = url.rstrip('/').split('/')[-1]
        page, _ = self._download_webpage_handle(url, video_id)
        results = re.findall("page: '(.+)'", page)
        formats = []
        for result in results:
            formats.extend(self._download_by_product_id(result, video_id))

        if not formats:
            raise ExtractorError('Could not find a POMS product id in the provided URL.')

        return {
            'id': video_id,
            'title': video_id,
            'formats': formats,
        }


class VPROIE(NPOIE):
    IE_NAME = 'vpro'
    IE_DESC = 'vpro.nl'
    _VALID_URL = r'https?://(?:www\.)?vpro.nl/.*'
    _TESTS = [{
        'url': 'https://www.vpro.nl/programmas/tegenlicht/kijk/afleveringen/2015-2016/offline-als-luxe.html',
        # TODO fill in other test attributes
    }]

    def _real_extract(self, url):
        video_id = url.rstrip('/').split('/')[-1]
        page, _ = self._download_webpage_handle(url, video_id)
        results = re.findall('data-media-id="(.+_.+)"\s', page)
        formats = []
        for result in results:
            formats.extend(self._download_by_product_id(result, video_id))
            break  # TODO find a better solution, VPRO pages can have multiple videos embedded

        if not formats:
            raise ExtractorError('Could not find a POMS product id in the provided URL.')

        return {
            'id': video_id,
            'title': video_id,
            'formats': formats,
        }


class ZAPPIE(NPOIE):
    IE_NAME = 'zapp'
    IE_DESC = 'zapp.nl'
    _VALID_URL = r'https?://(?:www\.)?zapp.nl/.*'

    _TESTS = [{
        'url': 'https://www.zapp.nl/programmas/zappsport/gemist/AT_300003973',
        # TODO fill in other test attributes
    }]

    def _real_extract(self, url):
        video_id = url.rstrip('/').split('/')[-1]

        formats = self._download_by_product_id(url, video_id)

        return {
            'id': video_id,
            'title': video_id,
            'formats': formats,
        }
