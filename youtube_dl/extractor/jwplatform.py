# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import int_or_none


class JWPlatformIE(InfoExtractor):
    _VALID_URL = r'(?:https?://content\.jwplatform\.com/(?:feeds|players|jw6)/|jwplatform:)(?P<id>[a-zA-Z0-9]{8})'
    _TEST = {
        'url': 'http://content.jwplatform.com/players/nPripu9l-ALJ3XQCI.js',
        'md5': 'fa8899fa601eb7c83a64e9d568bdf325',
        'info_dict': {
            'id': 'nPripu9l',
            'ext': 'mov',
            'title': 'Big Buck Bunny Trailer',
            'description': 'Big Buck Bunny is a short animated film by the Blender Institute. It is made using free and open source software.',
            'upload_date': '20081127',
            'timestamp': 1227796140,
        }
    }

    @staticmethod
    def _extract_url(webpage):
        mobj = re.search(
            r'<script[^>]+?src=["\'](?P<url>(?:https?:)?//content.jwplatform.com/players/[a-zA-Z0-9]{8})',
            webpage)
        if mobj:
            return mobj.group('url')

    def _real_extract(self, url):
        video_id = self._match_id(url)
        json_data = self._download_json('http://content.jwplatform.com/feeds/%s.json' % video_id, video_id)
        video_data = json_data['playlist'][0]
        subtitles = {}
        for track in video_data['tracks']:
            if track['kind'] == 'captions':
                subtitles[track['label']] = [{'url': self._proto_relative_url(track['file'])}]

        formats = []
        for source in video_data['sources']:
            source_url = self._proto_relative_url(source['file'])
            source_type = source.get('type') or ''
            if source_type == 'application/vnd.apple.mpegurl':
                formats.extend(self._extract_m3u8_formats(
                    source_url, video_id, 'mp4', 'm3u8_native', fatal=False))
            elif source_type.startswith('audio'):
                formats.append({
                    'url': source_url,
                    'vcodec': 'none',
                })
            else:
                formats.append({
                    'url': source_url,
                    'width': int_or_none(source.get('width')),
                    'height': int_or_none(source.get('height')),
                })
        self._sort_formats(formats)

        return {
            'id': video_id,
            'title': video_data['title'],
            'description': video_data.get('description'),
            'thumbnail': self._proto_relative_url(video_data.get('image')),
            'timestamp': int_or_none(video_data.get('pubdate')),
            'subtitles': subtitles,
            'formats': formats,
        }
