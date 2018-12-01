# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import (
    compat_str,
    int_or_none,
    str_or_none,
    try_get,
    url_or_none,
)


class TikTokIE(InfoExtractor):
    _VALID_URL = r'https?://(?:m\.)?tiktok\.com/v/(?P<id>[0-9]+)'
    _TEST = {
        'url': 'https://m.tiktok.com/v/6606727368545406213.html',
        'md5': 'd584b572e92fcd48888051f238022420',
        'info_dict': {
            'id': '6606727368545406213',
            'ext': 'mp4',
            'title': 'Zureeal on TikTok',
            'thumbnail': r're:^https?://.*~noop.image',
            'description': '#bowsette#mario#cosplay#uk#lgbt#gaming#asian#bowsettecosplay',
            'uploader': 'Zureeal',
            'width': 540,
            'height': 960,
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        data = self._parse_json(
            self._search_regex(
                r'var\s+data\s*=\s*({.+?});', webpage, 'data'
            ), video_id)

        title = self._og_search_title(webpage)

        description = str_or_none(try_get(data, lambda x: x['desc']))
        width = int_or_none(try_get(data, lambda x: x['video']['width']))
        height = int_or_none(try_get(data, lambda x: x['video']['height']))

        formats = []

        for count, (key, label) in enumerate((('play_addr_lowbr', 'Low'), ('play_addr', 'Normal'), ('download_addr', 'Download')), -2):
            for format in try_get(data, lambda x: x['video'][key]['url_list']):
                format_url = url_or_none(format)
                if not format_url:
                    continue
                formats.append({
                    'url': format_url,
                    'ext': 'mp4',
                    'height': height,
                    'width': width,
                    'format_note': label,
                    'quality': count
                })

        self._sort_formats(formats)

        uploader = try_get(data, lambda x: x['author']['nickname'], compat_str)

        thumbnail = url_or_none(
            try_get(
                data, lambda x: x['video']['cover']['url_list'][0], compat_str))

        return {
            'id': video_id,
            'title': title,
            'description': description,
            'uploader': uploader,
            'formats': formats,
            'thumbnail': thumbnail,
            'width': width,
            'height': height,
        }
