# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor

from ..utils import (
    float_or_none,
    int_or_none,
    url_or_none,
)


class TelewebionIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?telewebion\.com/(episode|clip)/(?P<id>[a-zA-Z0-9]+)'

    _TEST = {
        'url': 'http://www.telewebion.com/episode/0x1b3139c/',
        'info_dict': {
            'id': '0x1b3139c',
            'ext': 'mp4',
            'title': 'قرعه\u200cکشی لیگ قهرمانان اروپا',
            'thumbnail': r're:^https?://static\.telewebion\.com/episodeImages/.*/default',
            'view_count': int,
        },
        'params': {
            # m3u8 download
            'skip_download': True,
        },
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)

        episode_details = self._download_json('https://gateway.telewebion.ir/kandoo/episode/getEpisodeDetail/?EpisodeId={0}'.format(video_id), video_id)
        episode_details = episode_details['body']['queryEpisode'][0]

        channel_id = episode_details['channel']['descriptor']
        episode_image_id = episode_details.get('image')
        episode_image = 'https://static.telewebion.com/episodeImages/{0}/default'.format(episode_image_id) if episode_image_id else None

        m3u8_url = 'https://cdna.telewebion.com/{0}/episode/{1}/playlist.m3u8'.format(channel_id, video_id)
        formats = self._extract_m3u8_formats(
            m3u8_url, video_id, ext='mp4', m3u8_id='hls',
            entry_protocol='m3u8_native')
        self._sort_formats(formats)

        return {
            'id': video_id,
            'title': episode_details['title'],
            'formats': formats,
            'thumbnail': url_or_none(episode_image),
            'view_count': int_or_none(episode_details.get('view_count')),
            'duration': float_or_none(episode_details.get('duration')),
        }
