# coding: utf-8
from __future__ import unicode_literals

import json
import re

from .common import InfoExtractor
from ..utils import (
    int_or_none,
    ExtractorError,
)


class StreamMeIE(InfoExtractor):
    IE_NAME = 'StreamMe:video'
    _API_CHANNEL = 'https://www.stream.me/api-user/v1/<channel_id>/channel'
    _API_ARCHIVE = 'https://www.stream.me/api-vod/v1/<channel_id>/archives'
    _VALID_URL_BASE = r'https?://(video-cdn|www).stream.me'
    _VALID_URL = r'%s/archive/(?P<channel_id>[^/]+)/[^/]+/(?P<id>[^/?]+)' % _VALID_URL_BASE
    _TEST = {
        'url': 'https://www.stream.me/archive/kombatcup/kombat-cup-week-8-sunday-open/pDlXAj6mYb',
        'md5': 'b32af6fad972d0bcf5854a416b5b3b01',
        'info_dict': {
            'id': 'pDlXAj6mYb',
            'ext': 'mp4',
            'title': 'Kombat Cup Week #8 - Sunday Open',
            'uploader': 'KombatCup',
            'uploader_id': 'kombatcup',
            'timestamp': 1481512102000,
            'age_limit': 13,
        }
    }

    def _real_extract(self, url):
        m = re.match(self._VALID_URL, url)
        video_id = self._match_id(url)
        apiurl = self._API_ARCHIVE.replace('<channel_id>', m.group('channel_id'))

        data = json.loads(self._download_webpage(apiurl, video_id))

        for vod in data.get('_embedded').get('vod'):
            vod_info = []
            if vod.get('urlId') == video_id:
                vod_info = vod
                break

        manifest_json = self._download_json(vod_info
                                            .get('_links')
                                            .get('manifest')
                                            .get('href'), video_id)

        formats = self._extract_formats(manifest_json.get('formats'))
        self._sort_formats(formats, 'vbr')
        info = self._extract_info(vod_info)
        info['formats'] = formats
        return info

    def _extract_info(self, info):
        return {
            'id': info.get('urlId') or 'live',
            # 'formats': self.formats,
            'title': info.get('title'),
            'age_limit': int_or_none(info.get('ageRating')),
            'description': info.get('description') or None,
            'dislike_count': int_or_none(info.get('stats').get('raw').get('dislikes')),
            'display_id': info.get('titleSlug') or None,
            'duration': int_or_none(info.get('duration')),
            'like_count': int_or_none(info.get('stats').get('raw').get('likes')),
            'thumbnail': info.get('_links').get('thumbnail').get('href') or None,
            'timestamp': info.get('whenCreated') or None,
            'uploader': info.get('username') or None,
            'uploader_id': info.get('userSlug') or None,
            'view_count': int_or_none(info.get('stats').get('raw').get('views')),
            'is_live': True if info.get('active') else False,
        }

    def _extract_formats(self, fmts):
        formats = []
        for fmt_tag, d in fmts.items():
            # skip websocket and mjpeg we can't handle them anyway
            if fmt_tag in ('mjpeg-lodef', 'mp4-ws',):
                continue
            for fmt_info in d.get('encodings'):
                formats.append({
                    'url': fmt_info.get('location'),
                    'width': fmt_info.get('videoWidth'),
                    'height': fmt_info.get('videoHeight'),
                    'vbr': fmt_info.get('videoKbps'),
                    'abr': fmt_info.get('audioKbps'),
                    'acodec': d.get('audioCodec'),
                    'vcodec': d.get('videoCodec'),
                    'format_id': "%s%sp" % (fmt_tag, fmt_info.get('videoHeight')),
                    'ext': 'flv' if fmt_tag.split('-')[1] == 'rtmp' else 'mp4',
                    # I don't know all the possible protocols yet.
                    # 'protocol': 'm3u8_native' if fmt_tag == 'mp4-hls' else 'http'
                })
        return formats


class StreamMeLiveIE(StreamMeIE):
    IE_NAME = 'StreamIE:live'
    _VALID_URL = r'%s/(?P<id>[^\#]+$)' % StreamMeIE._VALID_URL_BASE

    def _real_extract(self, url):
        channel_id = self._match_id(url)
        apiurl = StreamMeIE._API_CHANNEL.replace('<channel_id>', channel_id)

        data = json.loads(self._download_webpage(apiurl, channel_id))
        stream_info = []
        # search for a live stream...
        for stream in data.get('_embedded').get('streams'):
            stream_info = stream
            break   # TODO: add to a list (multi-streams?)

        if not stream_info.get('active'):
            raise ExtractorError('%s is offline' % channel_id, expected=True)

        manifest_json = self._download_json(stream_info
                                            .get('_links')
                                            .get('manifest')
                                            .get('href'), channel_id)

        formats = self._extract_formats(manifest_json.get('formats'))
        self._sort_formats(formats, 'vbr')
        info = self._extract_info(stream_info)
        info['formats'] = formats
        return info


class StreamMeArchiveIE(StreamMeIE):
    IE_NAME = 'StreamMe:archives'
    _VALID_URL = r'%s/(?P<id>[^\#]+(?P<tag>\#archives)$)' % StreamMeIE._VALID_URL_BASE
    _PLAYLIST_TYPE = 'past broadcasts'
    _PLAYLIST_LIMIT = 128
    _TEST = {
        'url': 'https://www.stream.me/kombatcup#archives',
        'info_dict': {
            'id': 'kombatcup',
            'title': 'KombatCup',
        },
        'playlist_mincount': 25,
        'params': {
            'skip_download': True,
        }
    }

    def _real_extract(self, url):
        channel_id = self._match_id(url).split('#')[0]
        apiurl = StreamMeIE._API_ARCHIVE.replace('<channel_id>', channel_id)
        # TODO: implement paginated downloading
        data = json.loads(self._download_webpage(apiurl + '?limit=%d&offset=0' % self._PLAYLIST_LIMIT, channel_id))
        playlist = []

        for vod in data.get('_embedded').get('vod'):
            manifest_json = self._download_json(vod
                                                .get('_links')
                                                .get('manifest')
                                                .get('href'), vod.get('urlId'))
            formats = self._extract_formats(manifest_json.get('formats'))
            self._sort_formats(formats, 'vbr')
            info = self._extract_info(vod)
            info['formats'] = formats
            playlist.append(info)

        return self.playlist_result(playlist, channel_id, info.get('uploader'))
