# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import (
    determine_ext,
    int_or_none,
    merge_dicts,
    parse_iso8601,
    T,
    traverse_obj,
    txt_or_none,
    urljoin,
)


class CaffeineTVIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?caffeine\.tv/[^/]+/video/(?P<id>[0-9a-f-]+)'
    _TESTS = [{
        'url': 'https://www.caffeine.tv/TsuSurf/video/cffc0a00-e73f-11ec-8080-80017d29f26e',
        'info_dict': {
            'id': 'cffc0a00-e73f-11ec-8080-80017d29f26e',
            'ext': 'mp4',
            'title': 'GOOOOD MORNINNNNN #highlights',
            'timestamp': 1654702180,
            'upload_date': '20220608',
            'uploader': 'TsuSurf',
            'duration': 3145,
            'age_limit': 17,
        },
        'params': {
            'format': 'bestvideo',
        },
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        json_data = self._download_json(
            'https://api.caffeine.tv/social/public/activity/' + video_id,
            video_id)
        broadcast_info = traverse_obj(json_data, ('broadcast_info', T(dict))) or {}
        title = broadcast_info['broadcast_title']
        video_url = broadcast_info['video_url']

        ext = determine_ext(video_url)
        if ext == 'm3u8':
            formats = self._extract_m3u8_formats(
                video_url, video_id, 'mp4', entry_protocol='m3u8',
                fatal=False)
        else:
            formats = [{'url': video_url}]
        self._sort_formats(formats)

        return merge_dicts({
            'id': video_id,
            'title': title,
            'formats': formats,
        }, traverse_obj(json_data, {
            'uploader': ((None, 'user'), 'username'),
        }, get_all=False), traverse_obj(json_data, {
            'like_count': ('like_count', T(int_or_none)),
            'view_count': ('view_count', T(int_or_none)),
            'comment_count': ('comment_count', T(int_or_none)),
            'tags': ('tags', Ellipsis, T(txt_or_none)),
            'is_live': 'is_live',
            'uploader': ('user', 'name'),
        }), traverse_obj(broadcast_info, {
            'duration': ('content_duration', T(int_or_none)),
            'timestamp': ('broadcast_start_time', T(parse_iso8601)),
            'thumbnail': ('preview_image_path', T(lambda u: urljoin(url, u))),
            'age_limit': ('content_rating', T(lambda r: r and {
                # assume Apple Store ratings [1]
                # 1. https://en.wikipedia.org/wiki/Mobile_software_content_rating_system
                'FOUR_PLUS': 0,
                'NINE_PLUS': 9,
                'TWELVE_PLUS': 12,
                'SEVENTEEN_PLUS': 17,
            }.get(r, 17))),
        }))
