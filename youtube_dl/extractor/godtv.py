# coding: utf-8
from __future__ import unicode_literals

import re
from .common import InfoExtractor
from .ooyala import OoyalaIE


class GodTVIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?god\.tv(?:/[a-z0-9-]+)+/(?P<display_id>[a-z0-9-]+)'
    _TEST = {
        'url': 'http://god.tv/jesus-image/video/jesus-conference-2016/randy-needham',
        'info_dict': {
            'id': 'lpd3g2MzE6D1g8zFAKz8AGpxWcpu6o_3',
            'ext': 'mp4',
            'title': 'Randy Needham',
            'duration': 3615.08,
        },
        'params': {
            'skip_download': True,
        }
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        display_id = mobj.group('display_id')

        webpage = self._download_webpage(url, display_id)
        ooyala_id = self._search_regex(r'"content_id"\s*:\s*"([\w-]{32})"', webpage, display_id)

        return OoyalaIE._build_url_result(ooyala_id)
