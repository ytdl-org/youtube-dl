# encoding: utf-8
from __future__ import unicode_literals

from .nuevo import NuevoBaseIE

from ..compat import (
    compat_urllib_parse_unquote
)

import re


class TrollvidsIE(NuevoBaseIE):
    _VALID_URL = r"http://(?:www\.)?trollvids\.com/+video/+(?P<id>[0-9]+)/+(?P<title>[^?&]+)"
    IE_NAME = 'trollvids'

    def _real_extract(self, url):
        match = re.match(self._VALID_URL, url)

        video_id = match.group('id')
        raw_video_title = match.group('title')
        video_title = compat_urllib_parse_unquote(raw_video_title)
        url = "http://trollvids.com/video/%s/%s" % (video_id, raw_video_title)
        config_url = "http://trollvids.com/nuevo/player/config.php?v=%s" % video_id

        info = {
            "title": video_title,
            "webpage_url": url,
            "age_limit": 18
        }

        return self._extract_nuevo(config_url, video_id, info)

    _TESTS = [
        {
            'url': 'http://trollvids.com/video/2349002/%E3%80%90MMD-R-18%E3%80%91%E3%82%AC%E3%83%BC%E3%83%AB%E3%83%95%E3%83%AC%E3%83%B3%E3%83%89-carrymeoff',
            'md5': '1d53866b2c514b23ed69e4352fdc9839',
            'info_dict': {
                'id': '2349002',
                'ext': 'mp4',
                'title': "【MMD R-18】ガールフレンド carry_me_off",
                'age_limit': 18,
                'duration': 216.78,
            },
        },
    ]
