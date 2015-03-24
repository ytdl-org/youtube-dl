# encoding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import int_or_none


class MusicPlayOnIE(InfoExtractor):
    _VALID_URL = r'https?://(?:.+?\.)?musicplayon\.com/play(?:-touch)?\?(?:v|pl=100&play)=(?P<id>\d+)'

    _TEST = {
        'url': 'http://en.musicplayon.com/play?v=433377',
        'info_dict': {
            'id': '433377',
            'ext': 'mp4',
            'title': 'Rick Ross - Interview On Chelsea Lately (2014)',
            'description': 'Rick Ross Interview On Chelsea Lately',
            'duration': 342,
            'uploader': 'ultrafish',
        },
        'params': {
            # m3u8 download
            'skip_download': True,
        },
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')

        page = self._download_webpage(url, video_id)

        title = self._og_search_title(page)
        description = self._og_search_description(page)
        thumbnail = self._og_search_thumbnail(page)
        duration = self._html_search_meta('video:duration', page, 'duration', fatal=False)
        view_count = self._og_search_property('count', page, fatal=False)
        uploader = self._html_search_regex(
            r'<div>by&nbsp;<a href="[^"]+" class="purple">([^<]+)</a></div>', page, 'uploader', fatal=False)

        formats = [
            {
                'url': 'http://media0-eu-nl.musicplayon.com/stream-mobile?id=%s&type=.mp4' % video_id,
                'ext': 'mp4',
            }
        ]

        manifest = self._download_webpage(
            'http://en.musicplayon.com/manifest.m3u8?v=%s' % video_id, video_id, 'Downloading manifest')

        for entry in manifest.split('#')[1:]:
            if entry.startswith('EXT-X-STREAM-INF:'):
                meta, url, _ = entry.split('\n')
                params = dict(param.split('=') for param in meta.split(',')[1:])
                formats.append({
                    'url': url,
                    'ext': 'mp4',
                    'tbr': int(params['BANDWIDTH']),
                    'width': int(params['RESOLUTION'].split('x')[1]),
                    'height': int(params['RESOLUTION'].split('x')[-1]),
                    'format_note': params['NAME'].replace('"', '').strip(),
                })

        return {
            'id': video_id,
            'title': title,
            'description': description,
            'thumbnail': thumbnail,
            'uploader': uploader,
            'duration': int_or_none(duration),
            'view_count': int_or_none(view_count),
            'formats': formats,
        }
