# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor

from ..utils import (
    int_or_none,
    js_to_json,
    parse_iso8601,
    unified_strdate,
)


class RadioplayPodcastIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?radioplay\.(?:se|no)/podcast/[^/]+/[^/]+/(?P<id>\d+)'

    _TEST = {
        'url': 'https://radioplay.se/podcast/lilla-my/lyssna/2001126',
        'info_dict': {
            'id': '2001126',
            'ext': 'mp3',
            'title': 'Kaktus till läraren',
            'description': 'Lilla My ska köpa en "blomma" till sin lärare.',
            'timestamp': 1549898100,
            'upload_date': '20190211',
        },
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)
        player = self._parse_json(self._search_regex(
            r'window\.__PRELOADED_STATE__\s*=\s*({.+})', webpage,
            'player', default='{}'), video_id, transform_source=js_to_json)
        video_info = player['player']['nowPlaying']

        return {
            'url': video_info['PodcastExtMediaUrl'],
            'id': video_id,
            'title': video_info['PodcastTitle'],
            'description': video_info.get('PodcastDescription'),
            'thumbnail': video_info.get('PodcastImageUrl'),
            'release_date': unified_strdate(video_info.get('PodcastPublishDate')),
            'timestamp': parse_iso8601(video_info.get('PodcastPublishDate'), ' '),
            'duration': int_or_none(video_info.get('PodcastDuration')),
            'channel': player.get('podcastsApi').get('data').get('channel').get('PodcastChannelTitle'),
        }
