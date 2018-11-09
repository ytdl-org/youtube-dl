# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from .common import InfoExtractor

import re


class ChuunIE(InfoExtractor):
    _VALID_URL = r'https://chuun\.ctv\.co\.jp/player/(?P<id>\d+)'
    _TEST = {
        'url': 'https://chuun.ctv.co.jp/player/1',
        'md5': 'c989576b6b492df1eed57b5de290df23',
        'info_dict': {
            'id': '1',
            'ext': 'mp4',
            'title': '#0　中京テレビ放送　初来社　2015年8月23日配信分',
            'description': "太田上田 #0　中京テレビ放送　初来社　2015年8月23日配信分",
            'thumbnail': r're:^https?://.+\.(jpg|png)$',
        }
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')
        webpage = self._download_webpage(url, video_id)
        m3u8_url = re.findall(r"'movieAccessUrl':'(http[^']+)'", webpage)[0]
        title = self._og_search_title(webpage) or self._html_search_regex(r'<title>(.+)</title>', webpage, 'title')
        description = self._html_search_meta('description', webpage)
        thumbnail = self._og_search_thumbnail(webpage)\
            or self._html_search_regex(r"'programThumbnailUrlLarge':'(http[^']+)'", webpage, 'large_thumbnail')\
            or self._html_search_regex(r"'programThumbnailUrl':'(http[^']+)'", webpage, 'medium_thumbnail')\
            or self._html_search_regex(r"'programThumbnailUrlSmall':'(http[^']+)'", webpage, 'small_thumbnail')
        formats = self._extract_m3u8_formats(m3u8_url, video_id, ext='mp4')
        self._sort_formats(formats)
        return {
            'id': video_id,
            'url': url,
            'title': title,
            'description': description,
            'thumbnail': thumbnail,
            'formats': formats,
        }
