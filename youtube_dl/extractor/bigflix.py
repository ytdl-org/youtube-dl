# coding: utf-8
from __future__ import unicode_literals

from base64 import b64decode

from .common import InfoExtractor
from ..compat import compat_urllib_parse_unquote


class BigflixIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?bigflix\.com/.*/(?P<id>[0-9]+)'
    _TEST = {
        'url': 'http://www.bigflix.com/Hindi-movies/Action-movies/Singham-Returns/16537',
        'md5': 'ec76aa9b1129e2e5b301a474e54fab74',
        'info_dict': {
            'id': '16537',
            'ext': 'mp4',
            'title': 'Singham Returns',
            'description': 'md5:3d2ba5815f14911d5cc6a501ae0cf65d',
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)

        webpage = self._download_webpage(url, video_id)

        title = self._html_search_regex(
            r'<div[^>]+class=["\']pagetitle["\'][^>]*>(.+?)</div>',
            webpage, 'title')

        video_url = b64decode(compat_urllib_parse_unquote(self._search_regex(
            r'file=([^&]+)', webpage, 'video url')).encode('ascii')).decode('utf-8')

        description = self._html_search_meta('description', webpage)

        return {
            'id': video_id,
            'title': title,
            'url': video_url,
            'description': description,
        }
