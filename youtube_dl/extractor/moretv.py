# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..compat import compat_str
from ..utils import url_or_none


class MoreTVIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?more\.tv/(?P<id>[^/]+/[^/]+/[^/]+)'
    _TEST = {
        'url': 'https://more.tv/kuhnya_voina_za_otel/2_sezon/13_seriya',
        'md5': '18ddcd7b35cf5ad79a3938cb19cdc6ab',
        'info_dict': {
            'id': '1101454',
            'ext': 'mp4',
            'title': 'Кухня. Война за отель - 2 сезон, 13 серия',
            'thumbnail': r're:^https?://.*\.jpg(\?\d+)?$',
        },
        'file_minsize': None,
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        player_link = self._search_regex(r'"playerLink"\s*:\s*"([^"]*)"', webpage, 'player link')
        player = self._download_webpage(player_link, video_id)

        config = self._parse_json(
            self._search_regex(
                r'window\.ODYSSEUS_PLAYER_CONFIG\s*=\s*({.+?})[\s;]*window\.REQUEST_CONTEXT',
                player,
                'streams'
            ),
            video_id
        )

        item = config.get('data').get('playlist').get('items')[0]

        formats = []

        streams = item.get('streams')

        for stream in streams:
            stream_url = url_or_none(stream.get('url'))
            if not stream_url:
                continue

            stream_proto = stream.get('protocol')
            if not stream_proto:
                continue

            if stream_proto == 'HLS':
                formats.extend(self._extract_m3u8_formats(
                    stream_url, video_id, 'mp4', entry_protocol='m3u8_native',
                    m3u8_id='hls', fatal=False))
            if stream_proto == 'MSS':
                formats.extend(self._extract_ism_formats(
                    stream_url, video_id, ism_id='mss', fatal=False))
            elif stream_proto == 'DASH':
                formats.extend(self._extract_mpd_formats(
                    stream_url, video_id, mpd_id='dash', fatal=False))
            else:
                continue

        return {
            'id': compat_str(item.get('track_id')),
            'title': '%s - %s, %s' % (item.get('project_name'), item.get('season_name'), item.get('episode_name')),
            'formats': formats,
            'thumbnail': item.get('thumbnail_url')
        }
