# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..compat import compat_urllib_parse_unquote
from ..utils import (
    determine_ext,
    float_or_none,
    get_element_by_id,
    int_or_none,
    parse_iso8601,
    str_to_int,
)


class IzleseneIE(InfoExtractor):
    _VALID_URL = r'''(?x)
        https?://(?:(?:www|m)\.)?izlesene\.com/
        (?:video|embedplayer)/(?:[^/]+/)?(?P<id>[0-9]+)
        '''
    _TESTS = [
        {
            'url': 'http://www.izlesene.com/video/sevincten-cildirtan-dogum-gunu-hediyesi/7599694',
            'md5': '4384f9f0ea65086734b881085ee05ac2',
            'info_dict': {
                'id': '7599694',
                'ext': 'mp4',
                'title': 'Sevinçten Çıldırtan Doğum Günü Hediyesi',
                'description': 'md5:253753e2655dde93f59f74b572454f6d',
                'thumbnail': r're:^https?://.*\.jpg',
                'uploader_id': 'pelikzzle',
                'timestamp': int,
                'upload_date': '20140702',
                'duration': 95.395,
                'age_limit': 0,
            }
        },
        {
            'url': 'http://www.izlesene.com/video/tarkan-dortmund-2006-konseri/17997',
            'md5': '97f09b6872bffa284cb7fa4f6910cb72',
            'info_dict': {
                'id': '17997',
                'ext': 'mp4',
                'title': 'Tarkan Dortmund 2006 Konseri',
                'thumbnail': r're:^https://.*\.jpg',
                'uploader_id': 'parlayankiz',
                'timestamp': int,
                'upload_date': '20061112',
                'duration': 253.666,
                'age_limit': 0,
            }
        },
    ]

    def _real_extract(self, url):
        video_id = self._match_id(url)

        url = 'http://www.izlesene.com/video/%s' % video_id
        webpage = self._download_webpage(url, video_id)

        title = self._og_search_title(webpage)
        description = self._og_search_description(webpage, default=None)
        thumbnail = self._proto_relative_url(
            self._og_search_thumbnail(webpage), scheme='http:')

        uploader = self._html_search_regex(
            r"adduserUsername\s*=\s*'([^']+)';",
            webpage, 'uploader', fatal=False)
        timestamp = parse_iso8601(self._html_search_meta(
            'uploadDate', webpage, 'upload date'))

        duration = float_or_none(self._html_search_regex(
            r'"videoduration"\s*:\s*"([^"]+)"',
            webpage, 'duration', fatal=False), scale=1000)

        view_count = str_to_int(get_element_by_id('videoViewCount', webpage))
        comment_count = self._html_search_regex(
            r'comment_count\s*=\s*\'([^\']+)\';',
            webpage, 'comment_count', fatal=False)

        content_url = self._html_search_meta(
            'contentURL', webpage, 'content URL', fatal=False)
        ext = determine_ext(content_url, 'mp4')

        # Might be empty for some videos.
        streams = self._html_search_regex(
            r'"qualitylevel"\s*:\s*"([^"]+)"', webpage, 'streams', default='')

        formats = []
        if streams:
            for stream in streams.split('|'):
                quality, url = re.search(r'\[(\w+)\](.+)', stream).groups()
                formats.append({
                    'format_id': '%sp' % quality if quality else 'sd',
                    'url': compat_urllib_parse_unquote(url),
                    'ext': ext,
                })
        else:
            stream_url = self._search_regex(
                r'"streamurl"\s*:\s*"([^"]+)"', webpage, 'stream URL')
            formats.append({
                'format_id': 'sd',
                'url': compat_urllib_parse_unquote(stream_url),
                'ext': ext,
            })

        return {
            'id': video_id,
            'title': title,
            'description': description,
            'thumbnail': thumbnail,
            'uploader_id': uploader,
            'timestamp': timestamp,
            'duration': duration,
            'view_count': int_or_none(view_count),
            'comment_count': int_or_none(comment_count),
            'age_limit': self._family_friendly_search(webpage),
            'formats': formats,
        }
