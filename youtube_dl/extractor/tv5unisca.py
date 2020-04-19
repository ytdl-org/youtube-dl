# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor

from ..utils import (
    get_element_by_id
)

import re


class TV5UnisCaIE(InfoExtractor):
    IE_DESC = 'TV5UNISCA'
    _VALID_URL = r'https?://(?:www\.)?tv5unis\.ca/videos/(?P<id>[^?#]+)'
    _TESTS = []
    _GEO_COUNTRIES = ['CA', 'FR']

    def _real_extract(self, url):

        display_id = self._match_id(url)
        webpage = self._download_webpage(url, display_id)

        next_data_dict = self._parse_json(
            get_element_by_id('__NEXT_DATA__', webpage), display_id)\
            .get('props').get('apolloState')

        info_dict = self._json_ld(
            next_data_dict['$ArtisanBlocksPageMetaData:50.blockConfiguration.pageMetaDataConfiguration']['jsonLd'],
            display_id
        )

        formats = []
        for key in filter(lambda k: re.match(r'\$Video:\d+\.encodings\.', k), next_data_dict.keys()):
            url = next_data_dict[key].get('url')
            if not url:
                continue
            if url.endswith('.m3u8'):
                formats.extend(self._extract_m3u8_formats(url, display_id))
            if url.endswith('.ism/manifest'):
                formats.extend(self._extract_ism_formats(url, display_id, ism_id='mss', fatal=False))
            if url.endswith('.mp4'):
                formats.append({
                    'url': url,
                    'format_id': 'http'
                })

        info_dict['id'] = info_dict['display_id'] = display_id
        info_dict['formats'] = formats

        return info_dict
