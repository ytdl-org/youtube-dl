# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    js_to_json,
    get_element_by_class,
    unified_strdate,
)


class RudoIE(InfoExtractor):
    _VALID_URL = r'https?://rudo\.video/vod/(?P<id>[0-9a-zA-Z]+)'

    _TEST = {
        'url': 'http://rudo.video/vod/oTzw0MGnyG',
        'md5': '2a03a5b32dd90a04c83b6d391cf7b415',
        'info_dict': {
            'id': 'oTzw0MGnyG',
            'ext': 'mp4',
            'title': 'Comentario Tomás Mosciatti',
            'upload_date': '20160617',
        },
    }

    @classmethod
    def _extract_url(self, webpage):
        mobj = re.search(
            r'<iframe[^>]+src=(?P<q1>[\'"])(?P<url>(?:https?:)?//rudo\.video/vod/[0-9a-zA-Z]+)(?P=q1)',
            webpage)
        if mobj:
            return mobj.group('url')

    def _real_extract(self, url):
        video_id = self._match_id(url)

        webpage = self._download_webpage(url, video_id, encoding='iso-8859-1')

        jwplayer_data = self._parse_json(self._search_regex(
            r'(?s)playerInstance\.setup\(({.+?})\)', webpage, 'jwplayer data'), video_id,
            transform_source=lambda s: js_to_json(re.sub(r'encodeURI\([^)]+\)', '""', s)))

        info_dict = self._parse_jwplayer_data(
            jwplayer_data, video_id, require_title=False, m3u8_id='hls', mpd_id='dash')

        info_dict.update({
            'title': self._og_search_title(webpage),
            'upload_date': unified_strdate(get_element_by_class('date', webpage)),
        })

        return info_dict
