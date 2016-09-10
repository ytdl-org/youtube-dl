# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import (
    int_or_none,
    parse_duration,
    remove_end,
)


class LRTIE(InfoExtractor):
    IE_NAME = 'lrt.lt'
    _VALID_URL = r'https?://(?:www\.)?lrt\.lt/mediateka/irasas/(?P<id>[0-9]+)'
    _TESTS = [{
        'url': 'http://www.lrt.lt/mediateka/irasas/54391/',
        'info_dict': {
            'id': '54391',
            'ext': 'mp4',
            'title': 'Septynios Kauno dienos',
            'description': 'md5:24d84534c7dc76581e59f5689462411a',
            'duration': 1783,
            'view_count': int,
            'like_count': int,
            },
        'params': {
            'skip_download': True,  # m3u8 download
            },
        },
        {
            'url': 'http://www.lrt.lt/mediateka/irasas/1013074524',
            'info_dict': {
                'id': '1013074524',
                'ext': 'mp3',
                'title': 'Kita tema 2016-09-05 15:05',
                'duration': 3008,
                'description': 'md5:1b295a8fc7219ed0d543fc228c931fb5',
                },
            }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        title = remove_end(self._og_search_title(webpage), ' - LRT')
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


        m3u8_url = self._search_regex(
            r'\s+[^//]file\s*:\s*(["\'])(?P<url>.+?)\1\s*\+\s*location\.hash\.substring\(1\)',
            webpage, 'm3u8 url', group='url', default=None)
        if m3u8_url:
            formats = self._extract_m3u8_formats(m3u8_url, video_id, 'mp4')
            self._sort_formats(formats)

            return {
                    'id': video_id,
                    'title': title,
                    'formats': formats,
                    'thumbnail': thumbnail,
                    'description': description,
                    'duration': duration,
                    'view_count': view_count,
                    'like_count': like_count
            }
        else:
            mp3_url = self._search_regex(
                    r'\s+[^//]file\s*:\s*(["\'])(?P<url>.+?)\1',
                    webpage, 'mp3 url', group='url')
            return {
                    'id': video_id,
                    'ext': 'mp3',
                    'url': mp3_url,
                    'title': title,
                    'duration': duration,
                    'description': description,
                    'view_count': view_count,
                    'like_count': like_count
            }
