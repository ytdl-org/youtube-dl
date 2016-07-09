# encoding: utf-8
from __future__ import unicode_literals

import re

from .nuevo import NuevoBaseIE


class TrollvidsIE(NuevoBaseIE):
    _VALID_URL = r'https?://(?:www\.)?trollvids\.com/video/(?P<id>\d+)/(?P<display_id>[^/?#&]+)'
    IE_NAME = 'trollvids'
    _TEST = {
        'url': 'http://trollvids.com/video/2349002/%E3%80%90MMD-R-18%E3%80%91%E3%82%AC%E3%83%BC%E3%83%AB%E3%83%95%E3%83%AC%E3%83%B3%E3%83%89-carrymeoff',
        'md5': '1d53866b2c514b23ed69e4352fdc9839',
        'info_dict': {
            'id': '2349002',
            'ext': 'mp4',
            'title': '【MMD R-18】ガールフレンド carry_me_off',
            'age_limit': 18,
            'duration': 216.78,
        },
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')
        display_id = mobj.group('display_id')

        info = self._extract_nuevo(
            'http://trollvids.com/nuevo/player/config.php?v=%s' % video_id,
            video_id)
        info.update({
            'display_id': display_id,
            'age_limit': 18
        })
        return info
