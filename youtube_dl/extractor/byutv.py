from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import url_basename


class BYUtvIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?byutv\.org/(?:watch|player)/(?!event/)(?P<id>[0-9a-f-]+)(?:/(?P<display_id>[^/?#&]+))?'
    _TESTS = [{
        'url': 'http://www.byutv.org/watch/6587b9a3-89d2-42a6-a7f7-fd2f81840a7d/studio-c-season-5-episode-5',
        'info_dict': {
            'id': 'ZvanRocTpW-G5_yZFeltTAMv6jxOU9KH',
            'display_id': 'studio-c-season-5-episode-5',
            'ext': 'mp4',
            'title': 'Season 5 Episode 5',
            'description': 'md5:1d31dc18ef4f075b28f6a65937d22c65',
            'thumbnail': r're:^https?://.*',
            'duration': 1486.486,
        },
        'params': {
            'skip_download': True,
        },
        'add_ie': ['Ooyala'],
    }, {
        'url': 'https://www.byutv.org/player/a5467e14-c7f2-46f9-b3c2-cb31a56749c6/byu-soccer-w-argentina-vs-byu-4419',
        'info_dict': {
            'id': 'a5467e14-c7f2-46f9-b3c2-cb31a56749c6',
            'display_id': 'byu-soccer-w-argentina-vs-byu-4419',
            'ext': 'mp4',
            'title': 'Argentina vs. BYU (4/4/19)',
            'length': '02:05:43',
        },
    }, {
        'url': 'https://www.byutv.org/player/a5467e14-c7f2-46f9-b3c2-cb31a56749c6/byu-soccer-w-argentina-vs-byu-4419',
        'info_dict': {
            'id': 'a5467e14-c7f2-46f9-b3c2-cb31a56749c6',
            'display_id': 'byu-soccer-w-argentina-vs-byu-4419',
            'ext': 'mp4',
            'title': 'Argentina vs. BYU (4/4/19)',
            'length': '02:05:43',
        },
        'params': {
            'skip_download': True
        },
    }, {
        'url': 'http://www.byutv.org/watch/6587b9a3-89d2-42a6-a7f7-fd2f81840a7d',
        'only_matching': True,
    }, {
        'url': 'https://www.byutv.org/player/27741493-dc83-40b0-8420-e7ae38a2ae98/byu-football-toledo-vs-byu-93016?listid=4fe0fee5-0d3c-4a29-b725-e4948627f472&listindex=0&q=toledo',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')

        info = self._download_json(
            'https://api.byutv.org/api3/catalog/getvideosforcontent', video_id,
            query={
                'contentid': video_id,
                'channel': 'byutv',
                'x-byutv-context': 'web$US',
            }, headers={
                'x-byutv-context': 'web$US',
                'x-byutv-platformkey': 'xsaaw9c7y5',
            })

        if 'ooyalaVOD' in info:
            ep = info['ooyalaVOD']
            return {
                '_type': 'url_transparent',
                'ie_key': 'Ooyala',
                'url': 'ooyala:%s' % ep['providerId'],
                'id': video_id,
                'display_id': mobj.group('display_id') or video_id,
                'title': ep.get('title'),
                'description': ep.get('description'),
                'thumbnail': ep.get('imageThumbnail'),
            }
        elif 'dvr' in info:
            ep = info['dvr']
            formats = self._extract_m3u8_formats(
                ep['videoUrl'], video_id, 'mp4', entry_protocol='m3u8_native'
            )
            return {
                'formats': formats,
                'id': video_id,
                'display_id': url_basename(url),
                'title': ep.get('title'),
                'description': ep.get('description'),
                'thumbnail': ep.get('imageThumbnail'),
                'length': ep.get('length'),
            }
