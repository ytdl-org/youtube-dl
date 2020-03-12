# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import (
    clean_html,
    parse_filesize,
    float_or_none,
    int_or_none,
    unified_strdate,
    str_or_none,
    url_or_none,
    parse_duration,
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
            'creator': 'Magin Label',
            'view_count': int,
            'like_count': int,
            'dislike_count': int,
            'tags': list,
            'censored': 'True',
            'ext': 'mp4',
        },
        'params': {
            # m3u8 download
            'skip_download': True,
        },
    }

    def _real_extract(self, url):
        video_slug = self._match_id(url)

        webpage = self._download_webpage(url, video_slug)
        page_json = self._html_search_regex(r'window.__NUXT__=(.+?);<\/script>', webpage, 'Inline JSON')
        page_json = self._parse_json(page_json, video_slug).get('state').get('data').get('video').get('hentai_video')
        api_json = self._download_json(
            'https://members.hanime.tv/api/v3/videos_manifests/%s' % video_slug,
            video_slug,
            'API Call', headers={'X-Directive': 'api'}).get('videos_manifest').get('servers')[0].get('streams')

        title = page_json.get('name') or api_json.get[0].get('video_stream_group_id')
        tags = [t.get('text') for t in page_json.get('hentai_tags')]

        formats = []
        for f in api_json:
            item_url = url_or_none(f.get('url')) or url_or_none('https://hanime.tv/api/v1/m3u8s/%s.m3u8' % f.get('id'))
            format = [{
                'width': int_or_none(f.get('width')),
                'height': int_or_none(f.get('height')),
                'filesize_approx': parse_filesize('%sMb' % f.get('filesize_mbs')),
                'protocol': 'm3u8',
                'format_id': 'mp4-%sp' % f.get('height'),
                'tbr': float_or_none(float_or_none(f.get('filesize_mbs'), invscale=8388), int_or_none(f.get('duration_in_ms'), 1000)),
                'ext': 'mp4',
                'url': item_url,
            }, {
                'width': int_or_none(f.get('width')),
                'height': int_or_none(f.get('height')),
                'protocol': 'https',
                'format_id': 'm3u8-%sp' % f.get('height'),
                'format_note': '~8-50.00Kib',
                'ext': 'm3u8',
                'url': item_url,
            }]
            for i in format:
                formats.append(i)
        formats.reverse()

        return {
            'id': str_or_none(api_json[0].get('id')),
            'display_id': video_slug,
            'title': title,
            'description': clean_html(page_json.get('description')).strip(),
            'thumbnails': [
                {'preference': 0, 'id': 'Poster', 'url': url_or_none(page_json.get('poster_url'))},
                {'preference': 1, 'id': 'Cover', 'url': url_or_none(page_json.get('cover_url'))},
            ],
            'release_date': unified_strdate(page_json.get('released_at')),
            'upload_date': unified_strdate(page_json.get('created_at')),
            'creator': str_or_none(page_json.get('brand')),
            'view_count': int_or_none(page_json.get('views')),
            'like_count': int_or_none(page_json.get('likes')),
            'dislike_count': int_or_none(page_json.get('dislikes')),
            'duration': parse_duration('%sms' % f.get('duration_in_ms')),
            'tags': tags,
            'censored': str_or_none(page_json.get('is_censored')),
            'formats': formats,
        }
