# coding: utf-8

from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..compat import (
    compat_urllib_parse_unquote,
)
from ..utils import (
    unescapeHTML,
    js_to_json,
    int_or_none,
)


class PietsmietIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?pietsmiet\.de/gallery/(categories|playlists)/[\w-]+/(?P<id>\d+)-.*/?'
    _TESTS = [
        {
            'url': 'https://www.pietsmiet.de/gallery/categories/8-frag-pietsmiet/29844-fps-912',
            'info_dict': {
                'id': '29844',
                'ext': 'mp4',
                'title': 'Was würdet ihr die Maus fragen? 🎮 Frag PietSmiet #912',
            },
            'params': {
                'skip_download': True,  # m3u8 downloads
            }
        }, {
            'url': 'https://www.pietsmiet.de/gallery/playlists/646-metal-gear-solid-1/19804-metal-gear-solid-1-sniper-wolf-rematch',
            'info_dict': {
                'id': '19804',
                'ext': 'mp4',
                'title': 'SNIPER WOLF REMATCH 🎮 Metal Gear Solid #9'
            },
            'params': {
                'skip_download': True,  # m3u8 downloads
            }
        }
    ]

    def _real_extract(self, url):
        page_id = self._match_id(url)
        webpage = self._download_webpage(url, page_id)
        data_video_config = self._search_regex(
            r'var config =(.*?)\};\n', webpage, 'video config', flags=re.DOTALL)
        data_video_config = data_video_config.replace(']', '],', 1) + '}'
        data_video = self._parse_json(js_to_json(unescapeHTML(data_video_config)), page_id)

        formats = []

        m3u8_manifest_urls = filter(lambda x: x['file'].endswith('m3u8'), data_video['sources'])
        for f in m3u8_manifest_urls:
            m3u8_formats = self._extract_m3u8_formats(
                f['file'], page_id, 'mp4', 'm3u8_native', m3u8_id='hls')

            formats.extend(m3u8_formats)

        mp4_urls = filter(lambda x: not x['file'].endswith('m3u8'), data_video['sources'])
        for m in mp4_urls:
            label = m.get('label')
            format_height = 0

            if label:
                # Calculate resolution for HTTP format but should always be 1280x720
                format_height_raw = self._search_regex(
                    '([0-9]+)p', label, 'http video height',
                    default=720, fatal=False)
                format_height = int_or_none(format_height_raw)

            if format_height > 0:
                format_width = float(format_height) * (16 / 9)

                formats.append({
                    'format_id': 'http-{0}'.format(label),
                    'url': "https:{0}".format(m['file']),
                    'ext': m.get('type'),
                    'width': int_or_none(format_width),
                    'height': format_height,
                    'fps': 30.0,
                })
            else:
                formats.append({
                    'url': "https:{0}".format(m['file']),
                    'ext': m.get('type'),
                    'fps': 30.0,
                })

        self._sort_formats(formats)

        return {
            'id': page_id,
            'display_id': page_id,
            'title': compat_urllib_parse_unquote(data_video['abouttext']),
            'formats': formats,
            'thumbnail': 'http://www.pietsmiet.de/{0}'.format(data_video.get('image')),
        }
