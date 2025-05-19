# coding: utf-8
from __future__ import unicode_literals

import json
import re

from .common import InfoExtractor
from ..utils import ExtractorError, int_or_none, join_nonempty, merge_dicts, traverse_obj, url_or_none, T


class NPOIE(InfoExtractor):
    IE_NAME = 'npo'
    IE_DESC = 'npo.nl'
    _VALID_URL = r'https?://(?:www\.)?npo\.nl/start/serie/'

    _TESTS = [{
        'url': 'https://npo.nl/start/serie/zembla/seizoen-2015/wie-is-de-mol-2/',
        'md5': 'f9ce9c43cc8bc3b8138df1562b99c379',
        'info_dict': {
            'title': 'Wie is de mol? (2)',
            'thumbnail': 'https://assets-start.npo.nl/resources/2023/07/01/e723c3cf-3e42-418a-9ba5-f6dbb64b516a.jpg',
            'duration': 2439,
            'id': 'wie-is-de-mol-2',
            'description': 'wie-is-de-mol-2',
            'ext': 'mp4',
        }
    }, {
        'url': 'https://npo.nl/start/serie/vpro-tegenlicht/seizoen-11/zwart-geld-de-toekomst-komt-uit-afrika',
        'md5': 'c84d054219c4888ed53b4ee3d01b2d93',
        'info_dict': {
            'title': 'Zwart geld: de toekomst komt uit Afrika',
            'thumbnail': 'https://assets-start.npo.nl/resources/2023/06/30/d9879593-1944-4249-990c-1561dac14d8e.jpg',
            'duration': 3000,
            'id': 'zwart-geld-de-toekomst-komt-uit-afrika',
            'description': 'zwart-geld-de-toekomst-komt-uit-afrika',
            'ext': 'mp4',
        },
    }]

    def _get_token(self, video_id):
        return self._download_json(
            'https://npo.nl/start/api/domain/player-token?productId=%s' % video_id,
            video_id,
            note='Downloading token')['jwt']

    def _real_extract(self, url):
        # Remove /afspelen and/or any trailing `/`s
        url = re.sub(r'/(?:afspelen)?/*$', '', url)
        slug = url.split('/')[-1]

        program_metadata = self._download_json('https://npo.nl/start/api/domain/program-detail',
                                               slug, query={'slug': slug})
        product_id = traverse_obj(program_metadata, 'productId')
        if not product_id:
            raise ExtractorError('No productId found for slug: %s' % (slug,))
        formats = self._extract_formats_by_product_id(product_id, slug, url)
        self._sort_formats(formats)
        return merge_dicts(traverse_obj(program_metadata, {
            'title': 'title',
            'description': (('description', ('long', 'short', 'brief')), 'title'),
            'thumbnail': ('images', Ellipsis, 'url', T(url_or_none)),
            'duration': ('durationInSeconds', T(int_or_none)),
        }, get_all=False), {
            'id': slug,
            'formats': formats,
            'title': slug,
            'description': slug,
        })

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
    _TESTS = [
        {
            # 2025-05-19: This media is no longer available, see if it can be replaced with a different one
            #             where the GraphQL response has a pomsProductId
            'url': 'https://www.bnnvara.nl/videos/27455',
            'md5': '392dd367877739e49b9e0a9a550b178a',
            'info_dict': {
                'id': 'VARA_101369808',
                'thumbnail': 'https://media.vara.nl/files/thumbnails/321291_custom_zembla__wie_is_de_mol_680x383.jpg',
                'title': 'Zembla - Wie is de mol?',
                'ext': 'mp4',
            },
        },
        {
            'url': 'https://www.bnnvara.nl/videos/252209',
            'md5': 'f2d2a01d7de8fb490e177c9f71bbabc9',
            'info_dict': {
                'id': '252209',
                'thumbnail': 'https://media.bnnvara.nl/vara/images/thumbnails/20130502-dwdd-gesprek3_0.jpg',
                'title': 'Die Suid-Afrikaanse Droom: Nick en Simon - 2-5-2013',
                'ext': 'mp4',
            }
        },
    ]

    def _real_extract(self, url):
        url = url.rstrip('/')
        video_id = url.split('/')[-1]
        graphql_query = """query getMedia($id: ID!, $mediaUrl: String, $hasAdConsent: Boolean!, $atInternetId: Int) {
                            player(
                                id: $id
                                mediaUrl: $mediaUrl
                                hasAdConsent: $hasAdConsent
                                atInternetId: $atInternetId
                            ) {
                            ... on PlayerSucces {
                                brand {
                                    name
                                    slug
                                    broadcastsEnabled
                                    __typename
                                }
                                title
                                programTitle
                                pomsProductId
                                broadcasters {
                                    name
                                    __typename
                                }
                                duration
                                classifications {
                                    title
                                    imageUrl
                                    type
                                    __typename
                                }
                                image {
                                    title
                                    url
                                    __typename
                                }
                                cta {
                                    title
                                    url
                                    __typename
                                }
                                genres {
                                    name
                                    __typename
                                }
                                subtitles {
                                    url
                                    language
                                    __typename
                                }
                                sources {
                                    name
                                    url
                                    ratio
                                    __typename
                                }
                                    type
                                    token
                                    __typename
                                }
                                ... on PlayerError {
                                    error
                                    __typename
                                }
                                    __typename
                            }
}"""

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
                                            'query': graphql_query
                                        }).encode('utf8'),
                                    headers={
                                        'Content-Type': 'application/json',
                                    })

        mp4_url = traverse_obj(media, ('data', 'player', 'sources', 0, 'url'))
        if mp4_url:
            formats = [{'url': mp4_url}]
        else:
            product_id = traverse_obj(media, ('data', 'player', 'pomsProductId'))
            formats = self._extract_formats_by_product_id(product_id, video_id) if product_id else []
        self._sort_formats(formats)

        return {
            'id': video_id,
            'title': traverse_obj(media, ('data', 'player', 'title')),
            'formats': formats,
            'thumbnail': traverse_obj(media, ('data', 'player', 'image', 'url')),
        }


class ONIE(NPOIE):
    IE_NAME = 'on'
    IE_DESC = 'ongehoordnederland.tv'
    _VALID_URL = r'https?://(?:www\.)?ongehoordnederland.tv/.*'
    _TESTS = [{
        'url': 'https://ongehoordnederland.tv/2024/03/01/korte-clips/heeft-preppen-zin-betwijfel-dat-je-daar-echt-iets-aan-zult-hebben-bij-oorlog-lydia-daniel/',
        'md5': 'a85ebd50fa86fe5cbce654655f7dbb12',
        'info_dict': {
            'id': 'heeft-preppen-zin-betwijfel-dat-je-daar-echt-iets-aan-zult-hebben-bij-oorlog-lydia-daniel',
            'title': 'heeft-preppen-zin-betwijfel-dat-je-daar-echt-iets-aan-zult-hebben-bij-oorlog-lydia-daniel',
            'ext': 'mp4',
        },
    }]

    def _real_extract(self, url):
        video_id = url.rstrip('/').split('/')[-1]
        page = self._download_webpage(url, video_id)
        results = re.findall("page: '(.+)'", page)
        formats = []
        for result in results:
            formats.extend(self._extract_formats_by_product_id(result, video_id))

        self._sort_formats(formats)

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
        'url': 'https://www.zapp.nl/programmas/zappsport/gemist/POMS_AT_6130303',
        'md5': '3cef64f58b6b58eb34d5bd786f4e9245',
        'info_dict': {
            'id': 'POMS_AT_6130303',
            'title': 'POMS_AT_6130303',
            'ext': 'mp4',
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
            'title': 'Zapp Music Challenge 2015-Alain Clark & Yaell',
            'description': "Een nummer schrijven met de super bekende soulzanger en producer Alain Clark? Dat is de uitdaging voor de dertienjarige Yaell uit Delft. En als het dan echt goed is, mag hij het ook nog eens live gaan spelen op de speelplaats bij Giel Beelen! Muziek is heel erg belangrijk in het leven van Yaell. 'Als er geen muziek zou zijn, dan zou ik heel veel niet kunnen.' Hij is dan ook altijd aan het schrijven, vaak over zijn eigen leven. Maar soms is het best lastig om die teksten te verzinnen. Vindt hij de inspiratie om een hit te maken met Alain?",
            'ext': 'mp4',
        },
    }]

    def _real_extract(self, url):
        video_id = url.rstrip('/').split('/')[-1]

        build_id = self._search_nextjs_data(
            self._download_webpage(url, video_id),
            video_id,
        )['buildId']

        metadata_url = 'https://schooltv.nl/_next/data/' \
                       + build_id \
                       + '/video-item/' \
                       + video_id + '.json'

        metadata = self._download_json(metadata_url,
                                       video_id).get('pageProps', {}).get('data', {})

        formats = self._extract_formats_by_product_id(metadata.get('poms_mid'), video_id)

        self._sort_formats(formats)

        return {
            'id': video_id,
            'title': join_nonempty('title', 'subtitle', from_dict=metadata),
            'description': metadata.get('description') or metadata.get('short_description'),
            'formats': formats,
        }


class NTRSubsiteIE(NPOIE):
    def _real_extract(self, url):
        video_id = url.rstrip('/').split('/')[-1]

        page = self._download_webpage(url, video_id)
        results = re.findall(r'data-mid="(.+_.+)"', page)
        formats = []
        for result in results:
            formats.extend(self._extract_formats_by_product_id(result, video_id))
            break

        self._sort_formats(formats)

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
            'ext': 'mp4',
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
            'ext': 'mp4',
        },
    }]

    def _real_extract(self, url):
        video_id = url.rstrip('/').split('/')[-1]
        page = self._download_webpage(url, video_id)
        formats = traverse_obj(re.search(r'<[\w.-]+\s[^>]*(?<!-)\bdata-media-id="([a-zA-Z0-9_]+)"', page), (
                1, T(lambda x: self._extract_formats_by_product_id(x, video_id)),
                Ellipsis))

        self._sort_formats(formats)

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
            'ext': 'mp4',
        },
    }]
