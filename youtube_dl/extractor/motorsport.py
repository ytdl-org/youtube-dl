# coding: utf-8
from __future__ import unicode_literals

import hashlib
import json
import re
import time

from .common import InfoExtractor
from ..utils import (
    compat_parse_qs,
    compat_str,
    int_or_none,
)


class MotorsportIE(InfoExtractor):
    IE_DESC = 'motorsport.com'
    _VALID_URL = r'http://www\.motorsport\.com/[^/?#]+/video/(?:[^/?#]+/)(?P<id>[^/]+)/(?:$|[?#])'
    _TEST = {
        'url': 'http://www.motorsport.com/f1/video/main-gallery/red-bull-racing-2014-rules-explained/',
        'md5': '5592cb7c5005d9b2c163df5ac3dc04e4',
        'info_dict': {
            'id': '7063',
            'ext': 'mp4',
            'title': 'Red Bull Racing: 2014 Rules Explained',
            'duration': 207,
            'description': 'A new clip from Red Bull sees Daniel Ricciardo and Sebastian Vettel explain the 2014 Formula One regulations – which are arguably the most complex the sport has ever seen.',
            'uploader': 'rainiere',
            'thumbnail': r're:^http://.*motorsport\.com/.+\.jpg$'
        }
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        display_id = mobj.group('id')

        webpage = self._download_webpage(url, display_id)
        flashvars_code = self._html_search_regex(
            r'<embed id="player".*?flashvars="([^"]+)"', webpage, 'flashvars')
        flashvars = compat_parse_qs(flashvars_code)
        params = json.loads(flashvars['parameters'][0])

        e = compat_str(int(time.time()) + 24 * 60 * 60)
        base_video_url = params['location'] + '?e=' + e
        s = 'h3hg713fh32'
        h = hashlib.md5((s + base_video_url).encode('utf-8')).hexdigest()
        video_url = base_video_url + '&h=' + h

        uploader = self._html_search_regex(
            r'(?s)<span class="label">Video by: </span>(.*?)</a>', webpage,
            'uploader', fatal=False)

        return {
            'id': params['video_id'],
            'display_id': display_id,
            'title': params['title'],
            'url': video_url,
            'description': params.get('description'),
            'thumbnail': params.get('main_thumb'),
            'duration': int_or_none(params.get('duration')),
            'uploader': uploader,
        }
