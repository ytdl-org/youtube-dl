# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import float_or_none


class SpiegeltvIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?spiegel\.tv/(?:#/)?filme/(?P<id>[\-a-z0-9]+)'
    _TESTS = [{
        'url': 'http://www.spiegel.tv/filme/flug-mh370/',
        'info_dict': {
            'id': 'flug-mh370',
            'ext': 'm4v',
            'title': 'Flug MH370',
            'description': 'Das Rätsel um die Boeing 777 der Malaysia-Airlines',
            'thumbnail': 're:http://.*\.jpg$',
        },
        'params': {
            # rtmp download
            'skip_download': True,
        }
    }, {
        'url': 'http://www.spiegel.tv/#/filme/alleskino-die-wahrheit-ueber-maenner/',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        if '/#/' in url:
            url = url.replace('/#/', '/')
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)
        title = self._html_search_regex(r'<h1.*?>(.*?)</h1>', webpage, 'title')

        apihost = 'http://spiegeltv-ivms2-restapi.s3.amazonaws.com'
        version_json = self._download_json(
            '%s/version.json' % apihost, video_id,
            note='Downloading version information')
        version_name = version_json['version_name']

        slug_json = self._download_json(
            '%s/%s/restapi/slugs/%s.json' % (apihost, version_name, video_id),
            video_id,
            note='Downloading object information')
        oid = slug_json['object_id']

        media_json = self._download_json(
            '%s/%s/restapi/media/%s.json' % (apihost, version_name, oid),
            video_id, note='Downloading media information')
        uuid = media_json['uuid']
        is_wide = media_json['is_wide']

        server_json = self._download_json(
            'http://www.spiegel.tv/streaming_servers/', video_id,
            note='Downloading server information')
        server = server_json[0]['endpoint']

        thumbnails = []
        for image in media_json['images']:
            thumbnails.append({
                'url': image['url'],
                'width': image['width'],
                'height': image['height'],
            })

        description = media_json['subtitle']
        duration = float_or_none(media_json.get('duration_in_ms'), scale=1000)
        format = '16x9' if is_wide else '4x3'

        url = server + 'mp4:' + uuid + '_spiegeltv_0500_' + format + '.m4v'

        return {
            'id': video_id,
            'title': title,
            'url': url,
            'ext': 'm4v',
            'description': description,
            'duration': duration,
            'thumbnails': thumbnails
        }
