# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor


class ZypeIE(InfoExtractor):
    _VALID_URL = r'https?://player\.zype\.com/embed/(?P<id>[\da-fA-F]+)\.js\?.*?api_key=[^&]+'
    _TEST = {
        'url': 'https://player.zype.com/embed/5b400b834b32992a310622b9.js?api_key=jZ9GUhRmxcPvX7M3SlfejB6Hle9jyHTdk2jVxG7wOHPLODgncEKVdPYBhuz9iWXQ&autoplay=false&controls=true&da=false',
        'md5': 'eaee31d474c76a955bdaba02a505c595',
        'info_dict': {
            'id': '5b400b834b32992a310622b9',
            'ext': 'mp4',
            'title': 'Smoky Barbecue Favorites',
            'thumbnail': r're:^https?://.*\.jpe?g',
        },
    }

    @staticmethod
    def _extract_urls(webpage):
        return [
            mobj.group('url')
            for mobj in re.finditer(
                r'<script[^>]+\bsrc=(["\'])(?P<url>(?:https?:)?//player\.zype\.com/embed/[\da-fA-F]+\.js\?.*?api_key=.+?)\1',
                webpage)]

    def _real_extract(self, url):
        video_id = self._match_id(url)

        webpage = self._download_webpage(url, video_id)

        title = self._search_regex(
            r'video_title\s*[:=]\s*(["\'])(?P<value>(?:(?!\1).)+)\1', webpage,
            'title', group='value')

        m3u8_url = self._search_regex(
            r'(["\'])(?P<url>(?:(?!\1).)+\.m3u8(?:(?!\1).)*)\1', webpage,
            'm3u8 url', group='url')

        formats = self._extract_m3u8_formats(
            m3u8_url, video_id, 'mp4', entry_protocol='m3u8_native',
            m3u8_id='hls')
        self._sort_formats(formats)

        thumbnail = self._search_regex(
            r'poster\s*[:=]\s*(["\'])(?P<url>(?:(?!\1).)+)\1', webpage, 'thumbnail',
            default=False, group='url')

        return {
            'id': video_id,
            'title': title,
            'thumbnail': thumbnail,
            'formats': formats,
        }
