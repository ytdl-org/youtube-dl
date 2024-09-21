# coding: utf-8
from __future__ import unicode_literals

import json
import re

from .common import InfoExtractor
from ..utils import ExtractorError


class NPOIE(InfoExtractor):
    IE_NAME = 'npo'
    IE_DESC = 'npo.nl'
    _VALID_URL = r'https?://(?:www\.)?npo\.nl/start/serie/'

    _TESTS = [{
        'url': 'https://npo.nl/start/serie/zembla/seizoen-2015/wie-is-de-mol-2/',
        'md5': 'f9ce9c43cc8bc3b8138df1562b99c379',
        'info_dict': {
            'description': 'Wie is de mol? (2)',
            'duration': 2439,
            'ext': 'm4v',
            'id': 'wie-is-de-mol-2',
            'thumbnail': 'https://assets-start.npo.nl/resources/2023/07/01/e723c3cf-3e42-418a-9ba5-f6dbb64b516a.jpg',
            'title': 'Wie is de mol? (2)'
        }
    }, {
        'url': 'https://npo.nl/start/serie/vpro-tegenlicht/seizoen-11/zwart-geld-de-toekomst-komt-uit-afrika',
        'md5': 'c84d054219c4888ed53b4ee3d01b2d93',
        'info_dict': {
            'id': 'zwart-geld-de-toekomst-komt-uit-afrika',
            'title': 'Zwart geld: de toekomst komt uit Afrika',
            'ext': 'mp4',
            'description': 'Zwart geld: de toekomst komt uit Afrika',
            'thumbnail': 'https://assets-start.npo.nl/resources/2023/06/30/d9879593-1944-4249-990c-1561dac14d8e.jpg',
            'duration': 3000
        },
    }]

    def _get_token(self, video_id):
        return self._download_json(
            'https://npo.nl/start/api/domain/player-token?productId=%s' % video_id,
            video_id,
            note='Downloading token')['token']

    def _real_extract(self, url):
        # Remove /afspelen and/or any trailing `/`s
        url = re.sub(r'/(?:afspelen)?/*$', '', url)
        slug = url.split('/')[-1]

        program_metadata = self._download_json('https://npo.nl/start/api/domain/program-detail',
                                               slug, query={'slug': slug})
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

        formats = self._extract_formats_by_product_id(product_id, slug, url)

        return {
            'id': slug,
            'formats': formats,
            'title': title or slug,
            'description': description or title or slug,
            'thumbnail': thumbnail,
            'duration': duration,
        }

    def _extract_formats_by_product_id(self, product_id, slug, url=None):
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
                    'referrerUrl': url or '',
                }).encode('utf8'),
                headers={
                    'Authorization': token,
                    'Content-Type': 'application/json',
                },
                fatal=False,
            )
            stream_url = traverse_obj(stream_link, ('stream', 'streamURL'))
            formats.extend(self._extract_mpd_formats(stream_url, slug, mpd_id='dash', fatal=False))
        return formats


class BNNVaraIE(NPOIE):
    IE_NAME = 'bnnvara'
    IE_DESC = 'bnnvara.nl'
    _VALID_URL = r'https?://(?:www\.)?bnnvara\.nl/videos/[0-9]*'
    _TESTS = [{
        'url': 'https://www.bnnvara.nl/videos/27455',
        'md5': '392dd367877739e49b9e0a9a550b178a',
        'info_dict': {
            'id': 'VARA_101369808',
            'thumbnail': 'https://media.vara.nl/files/thumbnails/321291_custom_zembla__wie_is_de_mol_680x383.jpg',
            'title': 'Zembla - Wie is de mol?',
            'ext': 'mp4',
        }
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

        formats = self._extract_formats_by_product_id(product_id, video_id)

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
        'md5': 'a85ebd50fa86fe5cbce654655f7dbb12',
        'info_dict': {

        }
    }]

    def _real_extract(self, url):
        video_id = url.rstrip('/').split('/')[-1]
        page = self._download_webpage(url, video_id)
        results = re.findall("page: '(.+)'", page)
        formats = []
        for result in results:
            formats.extend(self._extract_formats_by_product_id(result, video_id))

        if not formats:
            raise ExtractorError('Could not find a POMS product id in the provided URL, '
                                 'perhaps because all stream URLs are DRM protected.')

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
        'url': 'https://www.zapp.nl/programmas/zappsport/gemist/POMS_AT_811523',
        'md5': '9eb2d8b6f88b72b6b986ea2c26a81588',
        'info_dict': {
            'id': 'POMS_AT_811523',
            'title': 'POMS_AT_811523',
        },
    }]

    def _real_extract(self, url):
        video_id = url.rstrip('/').split('/')[-1]

        formats = self._extract_formats_by_product_id(video_id, video_id, url=url)

        return {
            'id': video_id,
            'title': video_id,
            'formats': formats,
        }


class SchoolTVIE(NPOIE):
    IE_NAME = 'schooltv'
    IE_DESC = 'schooltv.nl'
    _VALID_URL = r'https?://(?:www\.)?schooltv.nl/item/.*'

    _TESTS = [{
        'url': 'https://schooltv.nl/item/zapp-music-challenge-2015-zapp-music-challenge-2015',
        'md5': 'e9ef151c4886994e2bea23593348cb14',
        'info_dict': {
            'id': 'zapp-music-challenge-2015-zapp-music-challenge-2015',
            'title': 'Zapp Music Challenge 2015 - Alain Clark & Yaell',
            'description': "Een nummer schrijven met de super bekende soulzanger en producer Alain Clark? Dat is de uitdaging voor de dertienjarige Yaell uit Delft. En als het dan echt goed is, mag hij het ook nog eens live gaan spelen op de speelplaats bij Giel Beelen! Muziek is heel erg belangrijk in het leven van Yaell. 'Als er geen muziek zou zijn, dan zou ik heel veel niet kunnen.' Hij is dan ook altijd aan het schrijven, vaak over zijn eigen leven. Maar soms is het best lastig om die teksten te verzinnen. Vindt hij de inspiratie om een hit te maken met Alain?"
        },
    }]

    def _real_extract(self, url):
        video_id = url.rstrip('/').split('/')[-1]

        # TODO Find out how we could obtain this automatically
        #      Otherwise this extractor might break each time SchoolTV deploys a new release
        build_id = 'b7eHUzAVO7wHXCopYxQhV'

        metadata_url = 'https://schooltv.nl/_next/data/' \
                       + build_id \
                       + '/item/' \
                       + video_id + '.json'

        metadata = self._download_json(metadata_url,
                                       video_id).get('pageProps', {}).get('data', {})

        formats = self._extract_formats_by_product_id(metadata.get('poms_mid'), video_id)

        if not formats:
            raise ExtractorError('Could not find a POMS product id in the provided URL, '
                                 'perhaps because all stream URLs are DRM protected.')

        return {
            'id': video_id,
            'title': metadata.get('title', '') + ' - ' + metadata.get('subtitle', ''),
            'description': metadata.get('description') or metadata.get('short_description'),
            'formats': formats,
        }


class NTRSubsiteIE(NPOIE):
    def _real_extract(self, url):
        video_id = url.rstrip('/').split('/')[-1]

        page, _ = self._download_webpage_handle(url, video_id)
        results = re.findall(r'data-mid="(.+_.+)"', page)
        formats = []
        for result in results:
            formats.extend(self._extract_formats_by_product_id(result, video_id))
            break

        if not formats:
            raise ExtractorError('Could not find a POMS product id in the provided URL, '
                                 'perhaps because all stream URLs are DRM protected.')

        return {
            'id': video_id,
            'title': video_id,
            'formats': formats,
        }


class HetKlokhuisIE(NTRSubsiteIE):
    IE_NAME = 'hetklokhuis'
    IE_DESC = 'hetklokhuis.nl'
    _VALID_URL = r'https?://(?:www\.)?hetklokhuis\.nl/.*'
    _TESTS = [{
        'url': 'https://hetklokhuis.nl/dossier/142/zoek-het-uit/tv-uitzending/2987/aliens',
        'md5': '4664b54ed4e05183b1e4f2f4290d551e',
        'info_dict': {
            'id': 'aliens',
            'title': 'aliens',
        },
    }]


class VPROIE(NPOIE):
    IE_NAME = 'vpro'
    IE_DESC = 'vpro.nl'
    _VALID_URL = r'https?://(?:www\.)?vpro.nl/.*'
    _TESTS = [{
        'url': 'https://www.vpro.nl/programmas/tegenlicht/kijk/afleveringen/2015-2016/offline-als-luxe.html',
        'md5': 'cf302e066b5313cfaf8d5adf50d64f13',
        'info_dict': {
            'id': 'offline-als-luxe.html',
            'title': 'offline-als-luxe.html',
            'ext': 'm4v',
        },
    }]

    def _real_extract(self, url):
        video_id = url.rstrip('/').split('/')[-1]
        page, _ = self._download_webpage_handle(url, video_id)
        results = re.findall(r'data-media-id="([a-zA-Z0-9_]+)"\s', page)
        formats = []
        for result in results:
            formats.extend(self._extract_formats_by_product_id(result, video_id))
            break  # TODO find a better solution, VPRO pages can have multiple videos embedded

        if not formats:
            raise ExtractorError('Could not find a POMS product id in the provided URL, '
                                 'perhaps because all stream URLs are DRM protected.')

        return {
            'id': video_id,
            'title': video_id,
            'formats': formats,
        }


class AndereTijdenIE(NTRSubsiteIE):
    IE_NAME = 'anderetijden'
    IE_DESC = 'anderetijden.nl'
    _VALID_URL = r'https?://(?:www\.)?anderetijden\.nl/.*'
    _TESTS = [{
        'url': 'https://anderetijden.nl/programma/1/Andere-Tijden/aflevering/676/Duitse-soldaten-over-de-Slag-bij-Arnhem',
        'md5': '3d607b16e00b459156b4ab6e163dccd7',
        'info_dict': {
            'id': 'Duitse-soldaten-over-de-Slag-bij-Arnhem',
            'title': 'Duitse-soldaten-over-de-Slag-bij-Arnhem',
        },
    }]
