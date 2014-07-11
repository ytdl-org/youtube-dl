# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    compat_parse_qs,
    compat_urllib_request,
)


class ScreencastIE(InfoExtractor):
    _VALID_URL = r'https?://www\.screencast\.com/t/(?P<id>[a-zA-Z0-9]+)'
    _TEST = {
        'url': 'http://www.screencast.com/t/3ZEjQXlT',
        'md5': '917df1c13798a3e96211dd1561fded83',
        'info_dict': {
            'id': '3ZEjQXlT',
            'ext': 'm4v',
            'title': 'Color Measurement with Ocean Optics Spectrometers',
            'description': 'md5:240369cde69d8bed61349a199c5fb153',
            'thumbnail': 're:^https?://.*\.jpg$'
        }
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')
        webpage = self._download_webpage(url, video_id)

        flash_vars_s = self._html_search_regex(
            r'<param name="flashVars" value="([^"]+)"', webpage, 'flash vars')
        flash_vars = compat_parse_qs(flash_vars_s)

        thumbnail = flash_vars.get('thumb', [None])[0]
        video_url_raw = compat_urllib_request.quote(flash_vars['content'][0])
        video_url = video_url_raw.replace('http%3A', 'http:')
        title = self._og_search_title(webpage)
        description = self._og_search_description(webpage)

        return {
            'id': video_id,
            'url': video_url,
            'title': title,
            'description': description,
            'thumbnail': thumbnail,
        }
