# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import url_basename
from ..compat import compat_urlparse


class VidbitIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?vidbit\.co/watch\?v=(?P<id>[\w-]+)'
    _TEST = {
        'url': 'http://www.vidbit.co/watch?v=MrM7LeaMJq',
        'md5': 'f1a579a93282a78de7e1c53220ef0f12',
        'info_dict': {
            'id': 'MrM7LeaMJq',
            'ext': 'mp4',
            'title': 'RoboCop (1987) - Dick You\'re Fired',
            'thumbnail': 'http://www.vidbit.co/thumbnails/MrM7LeaMJq.jpg',
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        return {
            'id': video_id,
            'title': self._html_search_regex(r'<h1>(.+)</h1>', webpage, 'title'),
            'url': compat_urlparse.urljoin(url, self._html_search_regex(r'file:\s*(["\'])((?:(?!\1).)+)\1',
                webpage, 'video URL', group=2)),
            'thumbnail': self._og_search_thumbnail(webpage),
            'description': self._html_search_regex(r'description:(["\'])((?:(?!\1).)+)\1',
                webpage, 'description', None, group=2),
        }
