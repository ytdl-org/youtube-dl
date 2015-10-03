# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..compat import compat_urllib_parse_unquote
from ..utils import (
    int_or_none,
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
                'thumbnail': 're:^http://.*\.jpg',
                'duration': 95395,
            }
        },
        {
            'url': 'http://www.izlesene.com/video/tarkan-dortmund-2006-konseri/17997',
            'md5': '97f09b6872bffa284cb7fa4f6910cb72',
            'info_dict': {
                'id': '17997',
                'ext': 'mp4',
                'title': 'Tarkan Dortmund 2006 Konseri',
                'thumbnail': 're:^http://.*\.jpg',
                'duration': 253666,
            }
        },
    ]

    def _real_extract(self, url):
        video_id = self._match_id(url)

        api_data = self._download_json('http://panel.izlesene.com/api/playerJson/izlesene/%s' % video_id, video_id)

        title = api_data['videoname']
        thumbnail = api_data.get('thumbnail')
        duration = int_or_none(api_data.get('videoduration'))
        view_count = int_or_none(str_to_int(api_data.get('views')))

        # Might be empty for some videos.
        streams = api_data.get('qualitylevel')

        formats = []
        # TODO: extract formats from dash manifest
        if streams:
            for stream in streams.split('|'):
                quality, url = re.search(r'\[(\w+)\](.+)', stream).groups()
                formats.append({
                    'format_id': '%sp' % quality if quality else 'sd',
                    'url': url,
                })
        else:
            stream_url = api_data.get('streamurl')
            formats.append({
                'format_id': 'sd',
                'url': stream_url,
            })

        return {
            'id': video_id,
            'title': title,
            'thumbnail': thumbnail,
            'duration': duration,
            'view_count': view_count,
            'formats': formats,
        }
