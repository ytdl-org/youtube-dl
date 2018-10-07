# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    NO_DEFAULT,
)


class MallTvIE(InfoExtractor):
    _VALID_URL = r'https://mall.tv/(?P<id>[^/#?]+)'
    _TEST = {
        'url': 'https://mall.tv/tajemstvi-nejkrupavejsich-kurecich-kridylek',
        'info_dict': {
            'id': 'tajemstvi-nejkrupavejsich-kurecich-kridylek',
            'ext': 'mp4',
            'title': 'Tajemství nejkřupavějších kuřecích křidýlek',
            'description': 'md5:f77cbb85d08745bfc85a2768fa34b57d',
            'thumbnail': r're:^https?://.*\.jpg',
            'duration': 58.0,
            'upload_date': '20180912',
            'timestamp': 1536781320,
        },
        'params': {
            # m3u8 download
            'skip_download': True,
        },
    }

    # MAll.tv has malformed type atribute (i.e. missing quotes)
    #
    JSON_LD_RE_MALLTV_MALFORMED = r'(?is)<script[^>]+type=application/ld\+json[^>]*>(?P<json_ld>.+?)</script>'

    def _search_json_ld(self, html, video_id, expected_type=None, **kwargs):
        json_ld = self._search_regex(
            self.JSON_LD_RE_MALLTV_MALFORMED, html, 'JSON-LD', group='json_ld', **kwargs)
        default = kwargs.get('default', NO_DEFAULT)
        if not json_ld:
            return default if default is not NO_DEFAULT else {}
        # JSON-LD may be malformed and thus `fatal` should be respected.
        # At the same time `default` may be passed that assumes `fatal=False`
        # for _search_regex. Let's simulate the same behavior here as well.
        fatal = kwargs.get('fatal', True) if default == NO_DEFAULT else False
        return self._json_ld(json_ld, video_id, fatal=fatal, expected_type=expected_type)

    def _real_extract(self, url):
        video_id = self._match_id(url)

        webpage = self._download_webpage(url, video_id)

        title = self._og_search_title(webpage, default=None)
        description = self._og_search_description(webpage, default=None)

        ldjson = self._search_json_ld(webpage, video_id, default=None)

        # Again, the malform attribute
        #
        source = self._search_regex(re.compile(r'<source\s+src=([^ \t]+)'), webpage, None, default=None)

        format_url = source + '.m3u8'
        formats = self._extract_m3u8_formats(format_url, video_id)
        for format in formats:
            format['ext'] = 'mp4'

        return {
            'id': video_id,
            'title': title,
            'description': description,
            'duration': ldjson['duration'],
            'timestamp': ldjson['timestamp'],
            'thumbnail': ldjson['thumbnail'],
            'formats': formats
        }
