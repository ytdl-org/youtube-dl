# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    merge_dicts,
    parse_iso8601,
)


class FilmarkIE(InfoExtractor):
    IE_NAME = 'Filmarkivet.se'
    _VALID_URL = r'https?://www\.filmarkivet\.se/movies/(?P<id>[\w-]+)'
    _TESTS = [{
        'url': 'https://www.filmarkivet.se/movies/paris-d-moll/',
        'md5': 'df02cadc719dcc63d43288366f037754',
        'info_dict': {
            'id': 'paris-d-moll',
            'ext': 'mp4',
            'upload_date': '20200602',
            'title': 'Paris d-moll',
            'description': 'md5:319e37ea5542293db37e1e13072fe330',
            'timestamp': 1591092663,
        }
    },
    ]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        title = (
            self._html_search_regex(r'<title\b[^>]*>\s*([^<]*)</title\b', webpage, '<title>', fatal=False)
            or self._og_search_title(webpage, fatal=False)
            or self._html_search_meta('twitter:title', webpage, default=''))
        title = re.split(r'(\s*-)?\s*[Ff]ilmarkivet', title, 1)[0] or self._generic_title(url)

        ld_json_info = self._search_json_ld(webpage, video_id, default={})

        jwp_info = self._extract_jwplayer_data(webpage, video_id, require_title=False)

        description = (
            self._og_search_description(webpage)
            or self._html_search_meta('twitter:description', webpage, default=None))
        timestamp = parse_iso8601(self._og_search_property('updated_time', webpage, default=None))

        return merge_dicts(
            jwp_info, ld_json_info, {
                'title': title,
                'description': description,
                'timestamp': timestamp,
            })
