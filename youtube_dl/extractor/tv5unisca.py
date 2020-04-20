# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor

from ..utils import (
    ExtractorError,
    get_element_by_id
)

import re


class TV5UnisCaIE(InfoExtractor):
    IE_DESC = 'TV5UNISCA'
    _VALID_URL = r'https?://(?:www\.)?tv5unis\.ca/videos/(?P<id>[^?#]+)'
    _TESTS = [{
        'url': 'https://www.tv5unis.ca/videos/expedition-kayak/saisons/1/episodes/2',
        'info_dict': {
            'id': 'expedition-kayak/saisons/1/episodes/2',
            'episode_number': 2,
            'season_number': 1,
            'ext': 'm3u8',
            'title': 'Expédition kayak - Gaspésie 2',
            'description': 'md5:aecf01897141d3997f10685b3f2662ef',
            'upload_date': '20200417',
            'timestamp': 1587085203,
        }
    }, {
        'url': 'https://www.tv5unis.ca/videos/la-bataille-de-notre-dame',
        'info_dict': {
            'id': 'la-bataille-de-notre-dame',
            'ext': 'm3u8',
            'title': 'La bataille de Notre-Dame',
            'description': 'md5:b69a25dbe9b1880eadad219af7372a7c',
            'upload_date': '20200414',
            'timestamp': 1586824384,
        },
        'params': {
            'skip_download': True,
        }
    }]
    _GEO_BYPASS = False

    def _real_extract(self, url):

        display_id = self._match_id(url)
        webpage = self._download_webpage(url, display_id)

        next_data_dict = self._parse_json(
            get_element_by_id('__NEXT_DATA__', webpage), display_id) \
            .get('props').get('apolloState')

        metadata = next_data_dict.get(
            '$ArtisanBlocksPageMetaData:50.blockConfiguration.pageMetaDataConfiguration', None
        )

        if not metadata:
            raise ExtractorError('Video removed or not found.', expected=True)

        info_dict = self._json_ld(metadata.get('jsonLd'), display_id)

        if info_dict.get('season', ''):
            info_dict['title'] = ' - '.join((info_dict.get('season', ''), info_dict.get('episode', '')))

        info_dict['id'] = info_dict['display_id'] = display_id

        formats = []
        for key in filter(lambda k: re.match(r'\$Video:\d+\.encodings\.', k), next_data_dict.keys()):
            url = next_data_dict[key].get('url')
            if not url:
                continue
            if url.endswith('.m3u8'):
                formats.extend(self._extract_m3u8_formats(url, display_id))
            if url.endswith('.mp4'):
                formats.append({
                    'url': url,
                    'format_id': 'http'
                })

        self._sort_formats(formats)
        info_dict['formats'] = formats

        return info_dict
