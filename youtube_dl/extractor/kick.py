# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import (
    float_or_none,
    int_or_none,
    parse_iso8601,
    strip_or_none,
    traverse_obj,
    url_or_none,
)


class KickIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?kick\.com/video/(?P<id>[0-9a-zA-Z-]+)'
    _TESTS = [{
        'url': 'https://kick.com/video/82a3c11d-7a17-4747-aecb-2e61413eb11f',
        'md5': 'f052bc1046cd9ca6751925dd12420010',
        'info_dict': {
            'id': '82a3c11d-7a17-4747-aecb-2e61413eb11f',
            'ext': 'mp4',
            'title': 'Weekly Stake Stream',
            'uploader': 'Eddie',
            'thumbnail': r're:^https?://.*\.jpg.*$',
            'timestamp': 1676890314,
            'upload_date': '20230220',
        }
    }]

    def _real_extract(self, url):
        id = self._match_id(url)

        headers = {
            'Accept': 'application/json',
        }

        data = self._download_json('https://kick.com/api/v1/video/%s' % id, id, headers=headers)

        formats = self._extract_m3u8_formats(
            data['source'], id, 'mp4')
        self._sort_formats(formats)
        livestream = data['livestream']
        strip_lambda = lambda x: strip_or_none(x) or None

        return {
            'id': id,
            'formats': formats,
            'title': livestream.get('session_title'),
            'uploader': traverse_obj(livestream, ('channel', 'user', 'username'), expected_type=strip_lambda),
            'thumbnail': url_or_none(livestream.get('thumbnail')),
            'duration': float_or_none(livestream.get('duration'), scale=1000),
            'timestamp': traverse_obj(data, 'updated_at', 'created_at', expected_type=parse_iso8601),
            'release_timestamp': parse_iso8601(data.get('created_at')),
            'view_count': int_or_none(data.get('views')),
            'is_live': livestream.get('is_live'),
            'channel': traverse_obj(livestream, ('channel', 'slug'), expected_type=strip_lambda),
            'categories': traverse_obj(data, ('categories', Ellipsis, 'name'), expected_type=strip_lambda) or None,
            'tags': traverse_obj(data, ('categories', Ellipsis, 'tags', Ellipsis), expected_type=strip_lambda) or None,
        }
