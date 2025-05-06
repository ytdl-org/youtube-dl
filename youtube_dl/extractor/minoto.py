# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    int_or_none,
    parse_codecs,
)


class MinotoIE(InfoExtractor):
    _VALID_URL = r'(?:minoto:|https?://(?:play|iframe|embed)\.minoto-video\.com/(?P<player_id>[0-9]+)/)(?P<id>[a-zA-Z0-9]+)'

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        player_id = mobj.group('player_id') or '1'
        video_id = mobj.group('id')
        video_data = self._download_json('http://play.minoto-video.com/%s/%s.js' % (player_id, video_id), video_id)
        video_metadata = video_data['video-metadata']
        formats = []
        for fmt in video_data['video-files']:
            fmt_url = fmt.get('url')
            if not fmt_url:
                continue
            container = fmt.get('container')
            if container == 'hls':
                formats.extend([fmt_url, video_id, 'mp4'], m3u8_id='hls', fatal=False)
            else:
                fmt_profile = fmt.get('profile') or {}
                formats.append({
                    'format_id': fmt_profile.get('name-short'),
                    'format_note': fmt_profile.get('name'),
                    'url': fmt_url,
                    'container': container,
                    'tbr': int_or_none(fmt.get('bitrate')),
                    'filesize': int_or_none(fmt.get('filesize')),
                    'width': int_or_none(fmt.get('width')),
                    'height': int_or_none(fmt.get('height')),
                    'codecs': parse_codecs(fmt.get('codecs')),
                })
        self._sort_formats(formats)

        return {
            'id': video_id,
            'title': video_metadata['title'],
            'description': video_metadata.get('description'),
            'thumbnail': video_metadata.get('video-poster', {}).get('url'),
            'formats': formats,
        }
