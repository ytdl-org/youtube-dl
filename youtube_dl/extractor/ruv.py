# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    determine_ext,
    unified_timestamp,
    int_or_none,
)


class RuvIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?ruv\.is/(?:spila/[^/]+|node)/(?P<id>[^/]+(?:/\d+)?)'
    _TESTS = [{
        # m3u8
        'url': 'http://www.ruv.is/spila/ruv/ferdastiklur/20190106',
        'md5': '26ba808bf9690f6f87c1469f6b6db8ab',
        'info_dict': {
            'id': '1338199',
            'display_id': 'ferdastiklur/20190106',
            'ext': 'mp4',
            'title': 'Ferðastiklur',
            'episode_number': 1,
            'description': 'md5:775b811c7cd3d7bf1509d5a4ff5edbcb',
            'timestamp': 1546803900,
            'upload_date': '20190106',
        },
    }, {
        # m3u8
        # No episode number
        'url': 'http://www.ruv.is/spila/ruv/vedur/20190117',
        'md5': '41cee6ef9c62955bba90b60f78a7de34',
        'info_dict': {
            'id': '1341887',
            'display_id': 'vedur/20190117',
            'ext': 'mp4',
            'title': 'Veður',
            'timestamp': 1547753400,
            'upload_date': '20190117',
        },
    }, {
        # mp3
        'url': 'http://www.ruv.is/spila/ras-1/i-ljosi-sogunnar/20190111',
        'md5': 'dbee43b6d480499421a37f65910d81b4',
        'info_dict': {
            'id': '1351187',
            'display_id': 'i-ljosi-sogunnar/20190111',
            'ext': 'mp3',
            'title': 'Í ljósi sögunnar',
            'description': 'md5:f79146f1737e21046b4f497ffd8c01b5',
            'timestamp': 1547197500,
            'upload_date': '20190111',
        },
    }, {
        'url': 'http://www.ruv.is/spila/ruv/frettir/20190117',
        'only_matching': True,
    }, {
        'url': 'http://www.ruv.is/node/1341894',
        'only_matching': True,
    }, {
        'url': 'http://www.ruv.is/spila/ras-1/lestin/20190117',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        display_id = self._match_id(url)

        webpage = self._download_webpage(url, display_id)

        title = self._og_search_title(webpage)

        episode = int_or_none(self._html_search_regex(
            r'<h3[^>].+\((\d+)+\s*\w{2}\s*\d+\)',
            webpage,
            'episode number',
            default=None,
        ))

        FIELD_RE = r'sources{0}\[(?:.*src{0}(["\'])(?P<url>(?:(?!\1).)+)\1.*\])'

        media_url = self._html_search_regex(
            FIELD_RE.format('\\s*:\\s*'),
            webpage,
            'video URL',
            group='url',
            flags=re.DOTALL,
        )

        video_id = self._search_regex(
            r'<link\b[^>]+\bhref=["\']https?://www\.ruv\.is/node/(\d+)',
            webpage, 'video id', default=display_id)

        ext = determine_ext(media_url)

        if ext == 'm3u8':
            formats = self._extract_m3u8_formats(
                media_url, video_id, 'mp4', entry_protocol='m3u8_native',
                m3u8_id='hls')
        elif ext == 'mp3':
            formats = [{
                'format_id': 'mp3',
                'url': media_url,
                'vcodec': 'none',
            }]
        else:
            formats = [{
                'url': media_url,
            }]

        description = self._og_search_description(webpage, default=None)
        thumbnail = self._og_search_thumbnail(
            webpage, default=None) or self._search_regex(
            FIELD_RE % 'poster', webpage, 'thumbnail', fatal=False)
        timestamp = unified_timestamp(self._html_search_meta(
            'article:published_time', webpage, 'timestamp', fatal=False))

        return {
            'id': video_id,
            'display_id': display_id,
            'title': title,
            'description': description,
            'thumbnail': thumbnail,
            'timestamp': timestamp,
            'formats': formats,
            'episode_number': episode,
        }
