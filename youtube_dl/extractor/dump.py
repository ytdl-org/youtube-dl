# encoding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
)

class DumpIE(InfoExtractor):
    _VALID_URL = r'^https?://(?:www\.)?dump\.com/(?P<id>[a-zA-Z0-9]+)/'

    def _real_extract(self, url):
        m = re.match(self._VALID_URL, url)
        video_id = m.group('id')

        # Note: There is an easier-to-parse configuration at
        # http://www.aparat.com/video/video/config/videohash/%video_id
        # but the URL in there does not work

        webpage = self._download_webpage(url, video_id)

        try:
            video_url = re.findall(r'file","(.+?.flv)"', webpage)[-1]
        except IndexError:
            raise ExtractorError(u'No video URL found')

        thumb = re.findall('<meta property="og:image" content="(.+?)"',webpage)[0]

        title = self._search_regex(r'<b>([^"]+)</b>', webpage, u'title')

        return {
            'id': video_id,
            'title': title,
            'url': video_url,
            'ext': 'flv',
            'thumbnail': thumb,
        }
