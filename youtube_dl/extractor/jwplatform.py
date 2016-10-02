# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..compat import compat_urlparse
from ..utils import (
    determine_ext,
    float_or_none,
    int_or_none,
    js_to_json,
    mimetype2ext,
)


class JWPlatformBaseIE(InfoExtractor):
    @staticmethod
    def _find_jwplayer_data(webpage):
        # TODO: Merge this with JWPlayer-related codes in generic.py

        mobj = re.search(
            r'jwplayer\((?P<quote>[\'"])[^\'" ]+(?P=quote)\)\.setup\s*\((?P<options>[^)]+)\)',
            webpage)
        if mobj:
            return mobj.group('options')

    def _extract_jwplayer_data(self, webpage, video_id, *args, **kwargs):
        jwplayer_data = self._parse_json(
            self._find_jwplayer_data(webpage), video_id,
            transform_source=js_to_json)
        return self._parse_jwplayer_data(
            jwplayer_data, video_id, *args, **kwargs)

    def _parse_jwplayer_data(self, jwplayer_data, video_id=None, require_title=True,
                             m3u8_id=None, mpd_id=None, rtmp_params=None, base_url=None):
        # JWPlayer backward compatibility: flattened playlists
        # https://github.com/jwplayer/jwplayer/blob/v7.4.3/src/js/api/config.js#L81-L96
        if 'playlist' not in jwplayer_data:
            jwplayer_data = {'playlist': [jwplayer_data]}

        entries = []

        # JWPlayer backward compatibility: single playlist item
        # https://github.com/jwplayer/jwplayer/blob/v7.7.0/src/js/playlist/playlist.js#L10
        if not isinstance(jwplayer_data['playlist'], list):
            jwplayer_data['playlist'] = [jwplayer_data['playlist']]

        for video_data in jwplayer_data['playlist']:
            # JWPlayer backward compatibility: flattened sources
            # https://github.com/jwplayer/jwplayer/blob/v7.4.3/src/js/playlist/item.js#L29-L35
            if 'sources' not in video_data:
                video_data['sources'] = [video_data]

            this_video_id = video_id or video_data['mediaid']

            formats = []
            for source in video_data['sources']:
                source_url = self._proto_relative_url(source['file'])
                if base_url:
                    source_url = compat_urlparse.urljoin(base_url, source_url)
                source_type = source.get('type') or ''
                ext = mimetype2ext(source_type) or determine_ext(source_url)
                if source_type == 'hls' or ext == 'm3u8':
                    formats.extend(self._extract_m3u8_formats(
                        source_url, this_video_id, 'mp4', 'm3u8_native', m3u8_id=m3u8_id, fatal=False))
                elif ext == 'mpd':
                    formats.extend(self._extract_mpd_formats(
                        source_url, this_video_id, mpd_id=mpd_id, fatal=False))
                # https://github.com/jwplayer/jwplayer/blob/master/src/js/providers/default.js#L67
                elif source_type.startswith('audio') or ext in ('oga', 'aac', 'mp3', 'mpeg', 'vorbis'):
                    formats.append({
                        'url': source_url,
                        'vcodec': 'none',
                        'ext': ext,
                    })
                else:
                    height = int_or_none(source.get('height'))
                    if height is None:
                        # Often no height is provided but there is a label in
                        # format like 1080p.
                        height = int_or_none(self._search_regex(
                            r'^(\d{3,})[pP]$', source.get('label') or '',
                            'height', default=None))
                    a_format = {
                        'url': source_url,
                        'width': int_or_none(source.get('width')),
                        'height': height,
                        'ext': ext,
                    }
                    if source_url.startswith('rtmp'):
                        a_format['ext'] = 'flv'

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

            entries.append({
                'id': this_video_id,
                'title': video_data['title'] if require_title else video_data.get('title'),
                'description': video_data.get('description'),
                'thumbnail': self._proto_relative_url(video_data.get('image')),
                'timestamp': int_or_none(video_data.get('pubdate')),
                'duration': float_or_none(jwplayer_data.get('duration')),
                'subtitles': subtitles,
                'formats': formats,
            })
        if len(entries) == 1:
            return entries[0]
        else:
            return self.playlist_result(entries)


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
