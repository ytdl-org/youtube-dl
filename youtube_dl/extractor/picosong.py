# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import urljoin, parse_duration, parse_filesize


class PicosongIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?picosong\.com/(?P<id>[0-9A-Za-z]{4})'
    _TESTS = [{
        'url': 'http://picosong.com/7uer/',
        'md5': '7f2ee011ba3ca2ac180a35deb10feabf',
        'info_dict': {
            'id': '7uer',
            'ext': 'mp3',
            'artist': 'Xarlable',
            'title': 'Rock My Forum',
            'album': 'Epic',
            'genre': 'Howto & Style',
            'duration': 187.0,
            'filesize_approx': 4700000,
            'asr': 44100,
            'abr': 210,
        },
    }, {
        'url': 'http://picosong.com/i3gs/',
        'md5': 'd4ec5d64d97e28b45d2710c096c29f70',
        'info_dict': {
            'id': 'i3gs',
            'ext': 'mp3',
            'title': 'Rick.mp3',
            'duration': 26.0,
            'filesize_approx': 1020000,
            'asr': 48000,
            'abr': 320,
        },
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)

        page = self._download_webpage(url, video_id)
        download_path = self._search_regex(
            r'value="/static/swf/picoplayer\.swf\?file=([^"]+)"',
            page, 'url')
        download_url = urljoin(url, download_path)

        def extract_info_td(key, fatal=True):
            return self._html_search_regex(
                r'%s:</td>\s*<td class="value">([^<]*)</td>' % (key, ),
                page, key, fatal=fatal)

        title = extract_info_td('Title')
        if not title:
            title = extract_info_td('Filename')

        def parse_digits(digits, key, fatal=True):
            if digits is None:
                return None
            m = self._search_regex(r'(^[0-9]+)', digits, key, fatal=fatal)
            if m is None:
                return None
            return int(m)

        return {
            'id': video_id,
            'title': title,
            'artist': extract_info_td('Artist', fatal=False),
            'album': extract_info_td('Album', fatal=False),
            'genre': extract_info_td('Genre', fatal=False),
            'duration': parse_duration(extract_info_td('Length', fatal=False)),
            'filesize_approx': parse_filesize(extract_info_td('File size', fatal=False)),
            'abr': parse_digits(extract_info_td('Bitrate', fatal=False), 'Bitrate', fatal=False),
            'asr': parse_digits(extract_info_td('Sample Rate', fatal=False), 'Sample Rate', fatal=False),
            'url': download_url,
        }
