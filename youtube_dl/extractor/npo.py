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
                        npo:|
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
        next_data = json.loads(next_data)
        product_id, title, description, thumbnail = None, None, None, None
        for query in next_data['props']['pageProps']['dehydratedState']['queries']:
            if isinstance(query['state']['data'], list):
                for entry in query['state']['data']:
                    if entry['slug'] == slug:
                        product_id = entry.get('productId')
                        title = entry.get('title')
                        synopsis = entry.get('synopsis', {})
                        description = (
                            synopsis.get('long')
                            or synopsis.get('short')
                            or synopsis.get('brief')
                        )
                        thumbnails = entry.get('images')
                        for thumbnail_entry in thumbnails:
                            if 'url' in thumbnail_entry:
                                thumbnail = thumbnail_entry.get('url')
        if not product_id:
            raise ExtractorError('No productId found for slug: %s' % slug)

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
                    'referrerUrl': url,
                }).encode('utf8'),
                headers={
                    'Authorization': token,
                    'Content-Type': 'application/json',
                }
            )
            stream_url = stream_link.get('stream', {}).get('streamURL')
            formats.extend(self._extract_mpd_formats(stream_url, slug, mpd_id='dash', fatal=False))

        return {
            'id': slug,
            'formats': formats,
            'title': title or slug,
            'description': description,
            'thumbnail': thumbnail,
            # TODO fill in other metadata that's available
        }
