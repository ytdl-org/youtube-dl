# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..compat import compat_urllib_parse_unquote_plus
from ..utils import (
    js_to_json,
)


class KaraoketvIE(InfoExtractor):
    _VALID_URL = r'http://karaoketv\.co\.il/\?container=songs&id=(?P<id>[0-9]+)'
    _TEST = {
        'url': 'http://karaoketv.co.il/?container=songs&id=171568',
        'info_dict': {
            'id': '171568',
            'ext': 'mp4',
            'title': 'אל העולם שלך - רותם כהן - שרים קריוקי',
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        page_video_url = self._og_search_video_url(webpage, video_id)
        config_json = compat_urllib_parse_unquote_plus(self._search_regex(
            r'config=(.*)', page_video_url, 'configuration'))

        urls_info_json = self._download_json(
            config_json, video_id, 'Downloading configuration',
            transform_source=js_to_json)

        url = urls_info_json['playlist'][0]['url']

        return {
            'id': video_id,
            'title': self._og_search_title(webpage),
            'url': url,
        }
