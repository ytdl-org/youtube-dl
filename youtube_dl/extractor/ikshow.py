# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import re
import base64

from .common import InfoExtractor
from ..utils import js_to_json


class IkshowIE(InfoExtractor):
    IE_NAME = 'ikshow.net'
    _VALID_URL = r'http://ikshow\.net/shows/(?P<show_id>[^/]+)/(?P<episode_id>[^/]+)'

    _TEST = {
        'url': 'http://ikshow.net/shows/running-man/episode-273/',
        'info_dict': {
            'id': 'running-man-episode-273',
            'ext': 'mp4',
            'title': 'Running Man Ep 273 English Subtitle',
            'description': 'Free to watch and download Running Man Episode 273 with Eng Sub',
        }
    }

    def _extract_id(self, url):
        mobj = re.match(self._VALID_URL, url)
        return '%s-%s' % (mobj.group('show_id'), mobj.group('episode_id'))

    def _real_extract(self, url):
        video_id = self._extract_id(url)
        webpage = self._download_webpage(url, video_id)

        params = self._search_regex(
            r'''(?s)jwplayer\("mediaplayer"\)\.setup\((\{.*?\})\);''',
            webpage, 'video url')
        params = re.sub(r'window\.atob\(("[a-zA-Z0-9+/=]+")\)', '\\1', params)
        params = self._parse_json(params, video_id, transform_source=js_to_json)
        formats = [{
            'url': base64.b64decode(s['file']).decode('utf-8'),
            'ext': s['type'],
        } for s in params['sources']]
        self._sort_formats(formats)

        return {
            'id': video_id,
            'title': self._og_search_title(webpage),
            'description': self._html_search_meta('description', webpage),
            'formats': formats,
        }
