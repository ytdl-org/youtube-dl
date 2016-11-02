# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    determine_ext,
    int_or_none,
    parse_duration,
    remove_end,
)


class LRTIE(InfoExtractor):
    IE_NAME = 'lrt.lt'
    _VALID_URL = r'https?://(?:www\.)?lrt\.lt/mediateka/irasas/(?P<id>[0-9]+)'
    _TESTS = [{
        # m3u8 download
        'url': 'http://www.lrt.lt/mediateka/irasas/54391/',
        'md5': 'fe44cf7e4ab3198055f2c598fc175cb0',
        'info_dict': {
            'id': '54391',
            'ext': 'mp4',
            'title': 'Septynios Kauno dienos',
            'description': 'md5:24d84534c7dc76581e59f5689462411a',
            'duration': 1783,
            'view_count': int,
            'like_count': int,
        },
    }, {
        # direct mp3 download
        'url': 'http://www.lrt.lt/mediateka/irasas/1013074524/',
        'md5': '389da8ca3cad0f51d12bed0c844f6a0a',
        'info_dict': {
            'id': '1013074524',
            'ext': 'mp3',
            'title': 'Kita tema 2016-09-05 15:05',
            'description': 'md5:1b295a8fc7219ed0d543fc228c931fb5',
            'duration': 3008,
            'view_count': int,
            'like_count': int,
        },
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        title = remove_end(self._og_search_title(webpage), ' - LRT')

        formats = []
        for _, file_url in re.findall(
                r'file\s*:\s*(["\'])(?P<url>(?:(?!\1).)+)\1', webpage):
            ext = determine_ext(file_url)
            if ext not in ('m3u8', 'mp3'):
                continue
            # mp3 served as m3u8 produces stuttered media file
            if ext == 'm3u8' and '.mp3' in file_url:
                continue
            if ext == 'm3u8':
                formats.extend(self._extract_m3u8_formats(
                    file_url, video_id, 'mp4', entry_protocol='m3u8_native',
                    fatal=False))
            elif ext == 'mp3':
                formats.append({
                    'url': file_url,
                    'vcodec': 'none',
                })
        self._sort_formats(formats)

        thumbnail = self._og_search_thumbnail(webpage)
        description = self._og_search_description(webpage)
        duration = parse_duration(self._search_regex(
            r'var\s+record_len\s*=\s*(["\'])(?P<duration>[0-9]+:[0-9]+:[0-9]+)\1',
            webpage, 'duration', default=None, group='duration'))

        view_count = int_or_none(self._html_search_regex(
            r'<div[^>]+class=(["\']).*?record-desc-seen.*?\1[^>]*>(?P<count>.+?)</div>',
            webpage, 'view count', fatal=False, group='count'))
        like_count = int_or_none(self._search_regex(
            r'<span[^>]+id=(["\'])flikesCount.*?\1>(?P<count>\d+)<',
            webpage, 'like count', fatal=False, group='count'))

        return {
            'id': video_id,
            'title': title,
            'formats': formats,
            'thumbnail': thumbnail,
            'description': description,
            'duration': duration,
            'view_count': view_count,
            'like_count': like_count,
        }
