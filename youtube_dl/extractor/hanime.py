# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import (
    clean_html,
    parse_filesize,
    float_or_none,
    int_or_none,
    parse_iso8601,
    unified_strdate,
    str_or_none,
    parse_duration,
    sanitize_url,
    compat_str,
    try_get,
)


class HanimeIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?hanime\.tv/videos/hentai/(?P<id>.+)(?:\?playlist_id=.+)?'
    _TEST = {
        'url': 'https://hanime.tv/videos/hentai/kuroinu-1',
        'info_dict': {
            'id': '33964',
            'display_id': 'kuroinu-1',
            'title': 'Kuroinu 1',
            'description': 'md5:37d5bb20d4a0834bd147bc1bac588a0b',
            'thumbnail': r're:^https?://.*\.jpg$',
            'release_date': '20120127',
            'upload_date': '20140509',
            'timestamp': 1399624976,
            'creator': 'Magin Label',
            'view_count': int,
            'like_count': int,
            'dislike_count': int,
            'tags': list,
            'ext': 'mp4',
        },
        'params': {
            # m3u8 download
            'skip_download': True,
        },
    }

    def _real_extract(self, url):
        video_slug = self._match_id(url)
        page_json = self._html_search_regex(r'<script>.+__NUXT__=(.+?);<\/script>', self._download_webpage(url, video_slug), 'Inline JSON')
        page_json = try_get(self._parse_json(page_json, video_slug), lambda x: x['state']['data']['video']['hentai_video'], dict) or {}
        api_json = self._download_json(
            'https://members.hanime.tv/api/v3/videos_manifests/%s' % video_slug,
            video_slug,
            'API Call', headers={'X-Directive': 'api'}).get('videos_manifest').get('servers')[0].get('streams')
        title = page_json.get('name') or api_json.get[0].get('video_stream_group_id')
        tags = []
        for t in page_json.get('hentai_tags'):
            if t.get('text'):
                tags.append(t.get('text'))
        formats = []
        for f in api_json:
            item_url = sanitize_url(f.get('url')) or sanitize_url('https://hanime.tv/api/v1/m3u8s/%s.m3u8' % f.get('id'))
            width = int_or_none(f.get('width'))
            height = int_or_none(f.get('height'))
            format = {
                'width': width,
                'height': height,
                'filesize_approx': float_or_none(parse_filesize('%sMb' % f.get('filesize_mbs'))),
                'protocol': 'm3u8',
                'format_id': 'mp4-%sp' % f.get('height'),
                'ext': 'mp4',
                'url': item_url,
            }
            formats.append(format)
        formats.reverse()

        return {
            'id': compat_str(api_json[0].get('id')),
            'display_id': video_slug,
            'title': title,
            'description': clean_html(page_json.get('description')),
            'thumbnails': [
                {'preference': 0, 'id': 'Poster', 'url': page_json.get('poster_url')},
                {'preference': 1, 'id': 'Cover', 'url': page_json.get('cover_url')},
            ],
            'release_date': unified_strdate(page_json.get('released_at')),
            'upload_date': unified_strdate(page_json.get('created_at')),
            'timestamp': parse_iso8601(page_json.get('created_at')),
            'creator': str_or_none(page_json.get('brand')),
            'view_count': int_or_none(page_json.get('views')),
            'like_count': int_or_none(page_json.get('likes')),
            'dislike_count': int_or_none(page_json.get('dislikes')),
            'duration': float_or_none(parse_duration('%sms' % f.get('duration_in_ms'))),
            'tags': tags,
            'formats': formats,
        }
