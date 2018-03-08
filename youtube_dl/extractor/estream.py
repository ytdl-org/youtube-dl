# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    determine_ext,
    int_or_none,
    ExtractorError,
)


class EstreamIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?estream\.to(?:/embed\-|/)(?P<id>\w+)\.html'
    _TESTS = [{
        'url': 'https://estream.to/otxvk53yi03r.html',
        'md5': 'db1be915e969795930fffaf7a42128a4',
        'info_dict': {
            'id': 'otxvk53yi03r',
            'ext': 'mp4',
            'title': 'Watch giphy mp4',
        },
    }, {
        'url': 'https://estream.to/embed-0vorujhi39p7.html',
        'md5': '47580f5a1f265d1ad6ce8b4775efa702',
        'info_dict': {
            'id': '0vorujhi39p7',
            'ext': 'mp4',
            'title': 'Looking up at Palm Trees (Free to Use HD Stock Video Footage) DHNqqSlSs8A',
        },

    }, ]

    @staticmethod
    def _extract_dim(res):
        height = res.split('x')[1]
        width = res.split('x')[0]
        return(width, height)

    def _real_extract(self, url):
        video_id = self._match_id(url)

        webpage = self._download_webpage(url, video_id)

        if re.search(r'<title>', webpage):
            title = self._html_search_regex(r'<title>(.+?)</title>', webpage, 'title')
        else:
            title = self._html_search_regex(r'<video.+\=\"(.+)\"\s>', webpage, 'title')

        width, height = None, None

        formats = []
        for format_ in re.findall(r'<source\s(.*)/>', webpage):
            source = re.search(r'''src\=\"(?P<src>.+)\"\stype\='(?P<type>.+?)\'''', format_)

            ext = determine_ext(source.group('src'), default_ext=None)
            res = re.search(r'''res\=\'(?P<res>.+)\'''', format_)
            if res is not None:
                width, height = self._extract_dim(res.group('res'))

            formats.append({
                'url': source.group('src'),
                'ext': ext or 'mp4',
                'width': int_or_none(width),
                'height': int_or_none(height),
            })

        if not formats:
            if 'File not found' in webpage or 'deleted' in webpage:
                raise ExtractorError('File not found', expected=True, video_id=video_id)

        self._sort_formats(formats)
        return {
            'id': video_id,
            'title': title,
            'formats': formats,
        }
