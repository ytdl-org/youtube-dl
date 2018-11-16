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
            'title': 'Zureeal|TikTok|Global Video Community',
            'thumbnail': 'http://m-p16.akamaized.net/img/tos-maliva-p-0068/5e7a4ec40fb146888fa27aa8d78f86fd~noop.image',
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
                r'var data = ({.+?});', webpage, 'data'
            ), video_id)

        title = self._og_search_title(webpage)

        description = str_or_none(try_get(data, lambda x: x['desc']))
        width = int_or_none(try_get(data, lambda x: x['video']['width']))
        height = int_or_none(try_get(data, lambda x: x['video']['height']))

        formats = []

        def extract_formats(url_list):
            if url_list[0] is None:
                return
            for url in url_list[0]:
                formats.append({
                    'url': url,
                    'ext': 'mp4',
                    'height': height,
                    'width': width,
                    'format_note': url_list[1]
                })

        extract_formats((try_get(data, lambda x: x['video']['play_addr_lowbr']['url_list']), 'Low quality'))
        extract_formats((try_get(data, lambda x: x['video']['play_addr']['url_list']), 'Normal quality'))
        extract_formats((try_get(data, lambda x: x['video']['download_addr']['url_list']), 'Download quality'))

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
