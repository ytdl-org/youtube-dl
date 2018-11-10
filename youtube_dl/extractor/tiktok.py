# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import (
    compat_str,
    determine_ext,
    int_or_none,
    try_get,
    url_or_none,
    urlhandle_detect_ext
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
            'description': 'Zureeal has just created an awesome short video with ♬ original sound - joogieboy1596',
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
                r'var data = ({.+?});', webpage, 'json_string', webpage, 'data'
            ), video_id)

        title = self._og_search_title(webpage)
        description = self._og_search_description(webpage)

        width = int_or_none(try_get(data, lambda x: x['video']['width'], int))
        height = int_or_none(try_get(data, lambda x: x['video']['height'], int))

        formats = []

        for url in data['video']['play_addr']['url_list']:
            ext = determine_ext(url)
            if ext == 'unknown_video':
                urlh = self._request_webpage(
                    url, video_id, note='Determining extension'
                )
                ext = urlhandle_detect_ext(urlh)
                formats.append({
                    'url': url,
                    'ext': ext,
                    'height': height,
                    'width': width,
                    'quality': -2,
                    'format_note': "Normal quality",
                })

        for url in data['video']['download_addr']['url_list']:
            ext = determine_ext(url)
            if ext == 'unknown_video':
                urlh = self._request_webpage(
                    url, video_id, note='Determining extension'
                )
                ext = urlhandle_detect_ext(urlh)
                formats.append({
                    'url': url,
                    'ext': ext,
                    'height': height,
                    'width': width,
                    'quality': 1,
                    'format_note': "Download quality",
                })

        for url in data['video']['play_addr_lowbr']['url_list']:
            ext = determine_ext(url)
            if ext == 'unknown_video':
                urlh = self._request_webpage(
                    url, video_id, note='Determining extension'
                )
                ext = urlhandle_detect_ext(urlh)
                formats.append({
                    'url': url,
                    'ext': ext,
                    'height': height,
                    'width': width,
                    'quality': -3,
                    'format_note': "Low bitrate",
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
