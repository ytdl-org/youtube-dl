# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import (
    int_or_none,
    js_to_json,
    url_or_none,
)


class VOEIE(InfoExtractor):
    IE_NAME = 'voe'
    IE_DESC = 'VOE.SX'
    _VALID_URL = r'https?://voe\.sx/(e/)?(?P<id>[a-z0-9]+)'
    _TEST = {
        'url': 'https://voe.sx/e/ng7ja5n5n2y8',
        'info_dict': {
            'id': 'ng7ja5n5n2y8',
            'title': 'md5:a86687fb962742f04652aee19ad34e06',
            'thumbnail': r're:^https?://.*\.jpg$',
            'ext': 'm3u8',
        },
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)

        webpage = self._download_webpage(
            'https://voe.sx/e/%s' % video_id, video_id)

        sources = self._parse_json(
            self._search_regex(r'\bsources\s*=\s*(\{[^}]+\})', webpage, 'sources'),
            video_id, transform_source=js_to_json)

        title = self._search_regex(
            r'<title>(?:Watch\s+)?(?P<title>.+?)(?:-\s+VOE\s+\|.+)?</title>',
            webpage, 'title', group='title')

        formats = []

        f_url = url_or_none(sources.get('hls'))
        if f_url:
            formats.extend(self._extract_m3u8_formats(
                f_url, video_id, entry_protocol='m3u8_native', fatal=False))
        f_url = url_or_none(sources.get('mp4'))
        if f_url:
            formats.append({
                'url': f_url,
                'ext': 'mp4',
                'height': int_or_none(sources.get('video_height')),
            })

        self._sort_formats(formats)

        thumbnail = url_or_none(self._search_regex(
            r'(?:VOEPlayer.|data-)poster\s*=\s*(["\'])(?P<thumbnail>(?:(?!\1)\S)+)\1',
            webpage, 'thumbnail', group='thumbnail', default=None))

        return {
            'id': video_id,
            'title': title,
            'formats': formats,
            'thumbnail': thumbnail,
        }
