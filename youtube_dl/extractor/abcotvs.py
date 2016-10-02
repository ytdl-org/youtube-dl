# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    int_or_none,
    parse_iso8601,
)


class ABCOTVSIE(InfoExtractor):
    IE_NAME = 'abcotvs'
    IE_DESC = 'ABC Owned Television Stations'
    _VALID_URL = r'https?://(?:abc(?:7(?:news|ny|chicago)?|11|13|30)|6abc)\.com(?:/[^/]+/(?P<display_id>[^/]+))?/(?P<id>\d+)'
    _TESTS = [
        {
            'url': 'http://abc7news.com/entertainment/east-bay-museum-celebrates-vintage-synthesizers/472581/',
            'info_dict': {
                'id': '472581',
                'display_id': 'east-bay-museum-celebrates-vintage-synthesizers',
                'ext': 'mp4',
                'title': 'East Bay museum celebrates vintage synthesizers',
                'description': 'md5:a4f10fb2f2a02565c1749d4adbab4b10',
                'thumbnail': 're:^https?://.*\.jpg$',
                'timestamp': 1421123075,
                'upload_date': '20150113',
                'uploader': 'Jonathan Bloom',
            },
            'params': {
                # m3u8 download
                'skip_download': True,
            },
        },
        {
            'url': 'http://abc7news.com/472581',
            'only_matching': True,
        },
    ]

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')
        display_id = mobj.group('display_id') or video_id

        webpage = self._download_webpage(url, display_id)

        m3u8 = self._html_search_meta(
            'contentURL', webpage, 'm3u8 url', fatal=True).split('?')[0]

        formats = self._extract_m3u8_formats(m3u8, display_id, 'mp4')
        self._sort_formats(formats)

        title = self._og_search_title(webpage).strip()
        description = self._og_search_description(webpage).strip()
        thumbnail = self._og_search_thumbnail(webpage)
        timestamp = parse_iso8601(self._search_regex(
            r'<div class="meta">\s*<time class="timeago" datetime="([^"]+)">',
            webpage, 'upload date', fatal=False))
        uploader = self._search_regex(
            r'rel="author">([^<]+)</a>',
            webpage, 'uploader', default=None)

        return {
            'id': video_id,
            'display_id': display_id,
            'title': title,
            'description': description,
            'thumbnail': thumbnail,
            'timestamp': timestamp,
            'uploader': uploader,
            'formats': formats,
        }


class ABCOTVSClipsIE(InfoExtractor):
    IE_NAME = 'abcotvs:clips'
    _VALID_URL = r'https?://clips\.abcotvs\.com/(?:[^/]+/)*video/(?P<id>\d+)'
    _TEST = {
        'url': 'https://clips.abcotvs.com/kabc/video/214814',
        'info_dict': {
            'id': '214814',
            'ext': 'mp4',
            'title': 'SpaceX launch pad explosion destroys rocket, satellite',
            'description': 'md5:9f186e5ad8f490f65409965ee9c7be1b',
            'upload_date': '20160901',
            'timestamp': 1472756695,
        },
        'params': {
            # m3u8 download
            'skip_download': True,
        },
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        video_data = self._download_json('https://clips.abcotvs.com/vogo/video/getByIds?ids=' + video_id, video_id)['results'][0]
        title = video_data['title']
        formats = self._extract_m3u8_formats(
            video_data['videoURL'].split('?')[0], video_id, 'mp4')
        self._sort_formats(formats)

        return {
            'id': video_id,
            'title': title,
            'description': video_data.get('description'),
            'thumbnail': video_data.get('thumbnailURL'),
            'duration': int_or_none(video_data.get('duration')),
            'timestamp': int_or_none(video_data.get('pubDate')),
            'formats': formats,
        }
