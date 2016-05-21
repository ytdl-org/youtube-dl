# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    determine_ext,
    float_or_none,
    int_or_none,
)


class JWPlatformBaseIE(InfoExtractor):
    def _parse_jwplayer_data(self, jwplayer_data, video_id, require_title=True, m3u8_id=None, rtmp_params=None):
        video_data = jwplayer_data['playlist'][0]

        formats = []
        for source in video_data['sources']:
            source_url = self._proto_relative_url(source['file'])
            source_type = source.get('type') or ''
            if source_type in ('application/vnd.apple.mpegurl', 'hls') or determine_ext(source_url) == 'm3u8':
                formats.extend(self._extract_m3u8_formats(
                    source_url, video_id, 'mp4', 'm3u8_native', m3u8_id=m3u8_id, fatal=False))
            elif source_type.startswith('audio'):
                formats.append({
                    'url': source_url,
                    'vcodec': 'none',
                })
            else:
                a_format = {
                    'url': source_url,
                    'width': int_or_none(source.get('width')),
                    'height': int_or_none(source.get('height')),
                }
                if source_url.startswith('rtmp'):
                    a_format['ext'] = 'flv',

                    # See com/longtailvideo/jwplayer/media/RTMPMediaProvider.as
                    # of jwplayer.flash.swf
                    rtmp_url_parts = re.split(
                        r'((?:mp4|mp3|flv):)', source_url, 1)
                    if len(rtmp_url_parts) == 3:
                        rtmp_url, prefix, play_path = rtmp_url_parts
                        a_format.update({
                            'url': rtmp_url,
                            'play_path': prefix + play_path,
                        })
                    if rtmp_params:
                        a_format.update(rtmp_params)
                formats.append(a_format)
        self._sort_formats(formats)

        subtitles = {}
        tracks = video_data.get('tracks')
        if tracks and isinstance(tracks, list):
            for track in tracks:
                if track.get('file') and track.get('kind') == 'captions':
                    subtitles.setdefault(track.get('label') or 'en', []).append({
                        'url': self._proto_relative_url(track['file'])
                    })

        return {
            'id': video_id,
            'title': video_data['title'] if require_title else video_data.get('title'),
            'description': video_data.get('description'),
            'thumbnail': self._proto_relative_url(video_data.get('image')),
            'timestamp': int_or_none(video_data.get('pubdate')),
            'duration': float_or_none(jwplayer_data.get('duration')),
            'subtitles': subtitles,
            'formats': formats,
        }


class JWPlatformIE(JWPlatformBaseIE):
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
        return self._parse_jwplayer_data(json_data, video_id)
