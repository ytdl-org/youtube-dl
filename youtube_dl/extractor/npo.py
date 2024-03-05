from __future__ import unicode_literals

import json

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
)


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
        'url': 'http://www.npo.nl/de-mega-mike-mega-thomas-show/27-02-2009/VARA_101191800',
        'md5': 'da50a5787dbfc1603c4ad80f31c5120b',
        'info_dict': {
            'id': 'VARA_101191800',
            'ext': 'm4v',
            'title': 'De Mega Mike & Mega Thomas show: The best of.',
            'description': 'md5:3b74c97fc9d6901d5a665aac0e5400f4',
            'upload_date': '20090227',
            'duration': 2400,
        },
        'skip': 'Video gone',
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
        page = self._download_webpage(url, slug, 'Finding productId using slug: %s' % slug)
        # TODO find out what proper HTML parsing utilities are available in youtube-dl
        next_data = page.split('<script id="__NEXT_DATA__" type="application/json">')[1].split('</script>')[0]
        # TODO The data in this script tag feels like GraphQL, so there might be an easier way
        #      to get the product id, maybe using a GraphQL endpoint
        next_data = self._parse_json(next_data, slug)
        product_id, title, description, thumbnail = None, None, None, None
        for query in next_data['props']['pageProps']['dehydratedState']['queries']:
            if isinstance(query['state']['data'], list):
                for entry in query['state']['data']:
                    if entry['slug'] == slug:
                        product_id = entry.get('productId')
                        title = entry.get('title')
                        synopsis = entry.get('synopsis', {})
                        description = (synopsis.get('long')
                                       or synopsis.get('short')
                                       or synopsis.get('brief'))
                        thumbnails = entry.get('images')
                        for thumbnail_entry in thumbnails:
                            if 'url' in thumbnail_entry:
                                thumbnail = thumbnail_entry.get('url')
        if not product_id:
            raise ExtractorError('No productId found for slug: %s' % slug)

        formats = self._download_by_product_id(product_id, slug, url)

        return {
            'id': slug,
            'formats': formats,
            'title': title or slug,
            'description': description,
            'thumbnail': thumbnail,
            # TODO fill in other metadata that's available
        }

    def _download_by_product_id(self, product_id, slug, url=None):
        token = self._get_token(product_id)
        formats = []
        for profile in (
                'dash',
                # 'hls',  # TODO test what needs to change for 'hls' support
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
