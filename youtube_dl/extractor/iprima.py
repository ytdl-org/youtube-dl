# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import re
import time

from .common import InfoExtractor
from ..utils import (
    sanitized_Request,
)


class IPrimaIE(InfoExtractor):
    _VALID_URL = r'https?://play\.iprima\.cz/(?:.+/)?(?P<id>[^?#]+)'

    _TESTS = [{
        'url': 'http://play.iprima.cz/gondici-s-r-o-33',
        'info_dict': {
            'id': 'p136534',
            'ext': 'mp4',
            'title': 'Gondíci s. r. o. (34)',
            'description': 'md5:16577c629d006aa91f59ca8d8e7f99bd',
        },
        'params': {
            'skip_download': True,  # m3u8 download
        },
    }, {
        'url': 'http://play.iprima.cz/particka/particka-92',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')

        webpage = self._download_webpage(url, video_id)

        video_id = self._search_regex(r'data-product="([^"]+)">', webpage, 'real id')

        req = sanitized_Request(
            'http://play.iprima.cz/prehravac/init?_infuse=1'
            '&_ts=%s&productId=%s' % (round(time.time()), video_id))
        req.add_header('Referer', url)
        playerpage = self._download_webpage(req, video_id, note='Downloading player')

        m3u8_url = self._search_regex(r"'src': '([^']+\.m3u8)'", playerpage, 'm3u8 url')

        formats = self._extract_m3u8_formats(m3u8_url, video_id, ext='mp4')

        self._sort_formats(formats)

        return {
            'id': video_id,
            'title': self._og_search_title(webpage),
            'thumbnail': self._og_search_thumbnail(webpage),
            'formats': formats,
            'description': self._og_search_description(webpage),
        }
