from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    sanitized_Request,
    url_basename,
)


class KeezMoviesIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?keezmovies\.com/video/.+?(?P<id>[0-9]+)(?:[/?&]|$)'
    _TEST = {
        'url': 'http://www.keezmovies.com/video/petite-asian-lady-mai-playing-in-bathtub-1214711',
        'md5': '1c1e75d22ffa53320f45eeb07bc4cdc0',
        'info_dict': {
            'id': '1214711',
            'ext': 'mp4',
            'title': 'Petite Asian Lady Mai Playing In Bathtub',
            'age_limit': 18,
            'thumbnail': 're:^https?://.*\.jpg$',
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)

        req = sanitized_Request(url)
        req.add_header('Cookie', 'age_verified=1')
        webpage = self._download_webpage(req, video_id)

        # embedded video
        mobj = re.search(r'href="([^"]+)"></iframe>', webpage)
        if mobj:
            embedded_url = mobj.group(1)
            return self.url_result(embedded_url)

        video_title = self._html_search_regex(
            r'<h1 [^>]*>([^<]+)', webpage, 'title')
        flashvars = self._parse_json(self._search_regex(
            r'var\s+flashvars\s*=\s*([^;]+);', webpage, 'flashvars'), video_id)

        formats = []
        for height in (180, 240, 480):
            if flashvars.get('quality_%dp' % height):
                video_url = flashvars['quality_%dp' % height]
                a_format = {
                    'url': video_url,
                    'height': height,
                    'format_id': '%dp' % height,
                }
                filename_parts = url_basename(video_url).split('_')
                if len(filename_parts) >= 2 and re.match(r'\d+[Kk]', filename_parts[1]):
                    a_format['tbr'] = int(filename_parts[1][:-1])
                formats.append(a_format)

        age_limit = self._rta_search(webpage)

        return {
            'id': video_id,
            'title': video_title,
            'formats': formats,
            'age_limit': age_limit,
            'thumbnail': flashvars.get('image_url')
        }
