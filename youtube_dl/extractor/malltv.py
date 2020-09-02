# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import merge_dicts


class MallTVIE(InfoExtractor):
    _VALID_URL = r'https?://(?:(?:www|sk)\.)?mall\.tv/(?:[^/]+/)*(?P<id>[^/?#&]+)'
    _TESTS = [{
        'url': 'https://www.mall.tv/18-miliard-pro-neziskovky-opravdu-jsou-sportovci-nebo-clovek-v-tisni-pijavice',
        'md5': '1c4a37f080e1f3023103a7b43458e518',
        'info_dict': {
            'id': 't0zzt0',
            'display_id': '18-miliard-pro-neziskovky-opravdu-jsou-sportovci-nebo-clovek-v-tisni-pijavice',
            'ext': 'mp4',
            'title': '18 miliard pro neziskovky. Opravdu jsou sportovci nebo Člověk v tísni pijavice?',
            'description': 'md5:25fc0ec42a72ba602b602c683fa29deb',
            'duration': 216,
            'timestamp': 1538870400,
            'upload_date': '20181007',
            'view_count': int,
        }
    }, {
        'url': 'https://www.mall.tv/kdo-to-plati/18-miliard-pro-neziskovky-opravdu-jsou-sportovci-nebo-clovek-v-tisni-pijavice',
        'only_matching': True,
    }, {
        'url': 'https://sk.mall.tv/gejmhaus/reklamacia-nehreje-vyrobnik-tepla-alebo-spekacka',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        display_id = self._match_id(url)

        webpage = self._download_webpage(
            url, display_id, headers=self.geo_verification_headers())

        SOURCE_RE = r'(<source[^>]+\bsrc=(?:(["\'])(?:(?!\2).)+|[^\s]+)/(?P<id>[\da-z]+)/index)\b'
        video_id = self._search_regex(
            SOURCE_RE, webpage, 'video id', group='id')

        media = self._parse_html5_media_entries(
            url, re.sub(SOURCE_RE, r'\1.m3u8', webpage), video_id,
            m3u8_id='hls', m3u8_entry_protocol='m3u8_native')[0]

        info = self._search_json_ld(webpage, video_id, default={})

        return merge_dicts(media, info, {
            'id': video_id,
            'display_id': display_id,
            'title': self._og_search_title(webpage, default=None) or display_id,
            'description': self._og_search_description(webpage, default=None),
            'thumbnail': self._og_search_thumbnail(webpage, default=None),
        })
