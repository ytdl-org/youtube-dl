from __future__ import unicode_literals

import os

from .common import InfoExtractor
from ..compat import (
    compat_urllib_parse_unquote,
    compat_urlparse,
)
from ..utils import url_basename


class RtmpIE(InfoExtractor):
    IE_DESC = False  # Do not list
    _VALID_URL = r'(?i)rtmp[est]?://.+'

    _TESTS = [{
        'url': 'rtmp://cp44293.edgefcs.net/ondemand?auth=daEcTdydfdqcsb8cZcDbAaCbhamacbbawaS-bw7dBb-bWG-GqpGFqCpNCnGoyL&aifp=v001&slist=public/unsecure/audio/2c97899446428e4301471a8cb72b4b97--audio--pmg-20110908-0900a_flv_aac_med_int.mp4',
        'only_matching': True,
    }, {
        'url': 'rtmp://edge.live.hitbox.tv/live/dimak',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        video_id = compat_urllib_parse_unquote(os.path.splitext(url.rstrip('/').split('/')[-1])[0])
        title = compat_urllib_parse_unquote(os.path.splitext(url_basename(url))[0])
        return {
            'id': video_id,
            'title': title,
            'formats': [{
                'url': url,
                'ext': 'flv',
                'format_id': compat_urlparse.urlparse(url).scheme,
            }],
        }
