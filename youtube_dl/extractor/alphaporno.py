from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    parse_iso8601,
    parse_duration,
    parse_filesize,
    int_or_none,
    js_to_json,
)


class AlphaPornoIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?alphaporno\.com/videos/(?P<id>[^/]+)'
    _TEST = {
        'url': 'http://www.alphaporno.com/videos/sensual-striptease-porn-with-samantha-alexandra/',
        'md5': 'feb6d3bba8848cd54467a87ad34bd38e',
        'info_dict': {
            'id': '258807',
            'display_id': 'sensual-striptease-porn-with-samantha-alexandra',
            'ext': 'mp4',
            'title': 'Sensual striptease porn with Samantha Alexandra',
            'thumbnail': r're:https?://.*\.jpg$',
            'timestamp': 1418694611,
            'upload_date': '20141216',
            'duration': 387,
            'filesize_approx': 54120000,
            'tbr': 1145,
            'categories': list,
            'age_limit': 18,
        }
    }

    def _real_extract(self, url):
        display_id = self._match_id(url)

        webpage = self._download_webpage(url, display_id)

        video_id = re.sub(r'^https?://.*/embed/', '', self._html_search_meta('embedUrl', webpage, 'video id'))

        result = self._extract_jwplayer_data(webpage, video_id, require_title=False)

        title = self._search_regex(
            [r'<meta content="([^"]+)" itemprop="description">',
             r'class="title" itemprop="name">([^<]+)<'],
            webpage, 'title')
        timestamp = parse_iso8601(self._html_search_meta(
            'uploadDate', webpage, 'upload date'))
        duration = parse_duration(self._html_search_meta(
            'duration', webpage, 'duration'))
        filesize_approx = self._html_search_meta(
            'contentSize', webpage, 'file size')

        # bitrates are taken from the URL; the document only contains
        # a single value for the lowest quality
        for f in result.get('formats') or []:
            m = re.search(r'[?&]br=(\d+)', f.get('url') or '')
            if m:
                f['tbr'] = int(m.group(1))

        # filesizes are concatenated together in the meta tag
        if filesize_approx:
            filesizes = re.findall(r'\s*[\d.]+\s*[A-Za-z]+', filesize_approx)
            for f, size in zip(result.get('formats') or [], filesizes):
                f['filesize_approx'] = parse_filesize(size)

        categories = self._html_search_meta(
            'keywords', webpage, 'categories', default='').split(',')

        age_limit = self._rta_search(webpage)

        result.update({
            'display_id': display_id,
            'title': title,
            'timestamp': timestamp,
            'duration': duration,
            'categories': categories,
            'age_limit': age_limit,
        })
        return result
