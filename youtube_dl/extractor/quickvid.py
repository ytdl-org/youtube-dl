from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    compat_urlparse,
    determine_ext,
    int_or_none,
)


class QuickVidIE(InfoExtractor):
    _VALID_URL = r'https?://(www\.)?quickvid\.org/watch\.php\?v=(?P<id>[a-zA-Z_0-9-]+)'
    _TEST = {
        'url': 'http://quickvid.org/watch.php?v=sUQT3RCG8dx',
        'md5': 'c0c72dd473f260c06c808a05d19acdc5',
        'info_dict': {
            'id': 'sUQT3RCG8dx',
            'ext': 'mp4',
            'title': 'Nick Offerman\'s Summer Reading Recap',
            'thumbnail': 're:^https?://.*\.(?:png|jpg|gif)$',
            'view_count': int,
        },
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        title = self._html_search_regex(r'<h2>(.*?)</h2>', webpage, 'title')
        view_count = int_or_none(self._html_search_regex(
            r'(?s)<div id="views">(.*?)</div>',
            webpage, 'view count', fatal=False))
        video_code = self._search_regex(
            r'(?s)<video id="video"[^>]*>(.*?)</video>', webpage, 'video code')
        formats = [
            {
                'url': compat_urlparse.urljoin(url, src),
                'format_id': determine_ext(src, None),
            } for src in re.findall('<source\s+src="([^"]+)"', video_code)
        ]
        self._sort_formats(formats)

        return {
            'id': video_id,
            'title': title,
            'formats': formats,
            'thumbnail': self._og_search_thumbnail(webpage),
            'view_count': view_count,
        }
