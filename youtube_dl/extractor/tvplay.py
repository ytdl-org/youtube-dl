# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    parse_iso8601,
    qualities,
)


class TVPlayIE(InfoExtractor):
    _VALID_URL = r'http://(?:www\.)?tvplay\.lv/parraides/[^/]+/(?P<id>\d+)'
    _TESTS = [
        {
            'url': 'http://www.tvplay.lv/parraides/vinas-melo-labak/418113?autostart=true',
            'info_dict': {
                'id': '418113',
                'ext': 'flv',
                'title': 'Kādi ir īri? - Viņas melo labāk',
                'description': 'Baiba apsmej īrus, kādi tie ir un ko viņi dara.',
                'duration': 25,
                'timestamp': 1406097056,
                'upload_date': '20140723',
            },
            'params': {
                # rtmp download
                'skip_download': True,
            },
        },
    ]

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')

        video = self._download_json(
            'http://playapi.mtgx.tv/v1/videos/%s' % video_id, video_id, 'Downloading video JSON')

        if video['is_geo_blocked']:
            raise ExtractorError(
                'This content is not available in your country due to copyright reasons', expected=True)

        streams = self._download_json(
            'http://playapi.mtgx.tv/v1/videos/stream/%s' % video_id, video_id, 'Downloading streams JSON')

        quality = qualities(['hls', 'medium', 'high'])
        formats = []
        for format_id, video_url in streams['streams'].items():
            if not video_url:
                continue
            fmt = {
                'format_id': format_id,
                'preference': quality(format_id),
            }
            if video_url.startswith('rtmp'):
                m = re.search(r'^(?P<url>rtmp://[^/]+/(?P<app>[^/]+))/(?P<playpath>.+)$', video_url)
                if not m:
                    continue
                fmt.update({
                    'ext': 'flv',
                    'url': m.group('url'),
                    'app': m.group('app'),
                    'play_path': m.group('playpath'),
                })
            else:
                fmt.update({
                    'url': video_url,
                })
            formats.append(fmt)

        self._sort_formats(formats)

        return {
            'id': video_id,
            'title': video['title'],
            'description': video['description'],
            'duration': video['duration'],
            'timestamp': parse_iso8601(video['created_at']),
            'view_count': video['views']['total'],
            'age_limit': video.get('age_limit', 0),
            'formats': formats,
        }
