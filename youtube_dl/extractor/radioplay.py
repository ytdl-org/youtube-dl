# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import (
    unified_strdate,
)


class RadioplayIE(InfoExtractor):
    IE_DESC = 'radioplay.fi'
    _VALID_URL = r'https?://(?:www\.)?radioplay\.fi/podcast/[^/]*/listen/(?P<id>\d+)/?'
    _TESTS = [
        {
            'url': 'https://radioplay.fi/podcast/auta-antti/listen/15723/',
            'md5': '6e194a6021132b1aed15a9faa3d55c8f',
            'info_dict': {
                'id': '15723',
                'ext': 'm4a',
                'title': 'Ystävyydestä',
                'description': 'md5:17b9893c3ad4b05360eb1dd3efd13a0c',
                'thumbnail': r're:^https?://.*\.jpg$',
                'duration': 3176,
                'upload_date': '20190405',
                'age_limit': 0,
                'season_number': 2,
                'episode_number': 3,
                'channel': 'Auta Antti!',
                'channel_id': '278',
            },
        },
    ]

    def _real_extract(self, url):
        episode_id = self._match_id(url)

        webpage = self._download_webpage(url, episode_id)
        _json = self._parse_json(self._search_regex(
            r'window\.__PRELOADED_STATE__\s*=\s*({.+})',
            webpage, 'nowPlaying'), episode_id)
        ep = _json['player']['nowPlaying']
        ch = _json['podcastsApi']['data']['channel']

        assert str(ep['PodcastRadioplayId']) == episode_id

        return {
            'id': episode_id,
            'title': ep['PodcastTitle'],
            'description': ep.get('PodcastDescription', None),
            'thumbnail': ep.get('PodcastImageUrl', None),
            'duration': ep.get('PodcastDuration', None),
            'upload_date': unified_strdate(ep.get('PodcastPublishDate', None)),
            'age_limit': 18 if ep.get('PodcastExplicit', 0) != 0 else 0,
            'season_number': ep.get('PodcastSeasonNumber', None),
            'episode': ep['PodcastTitle'],
            'episode_number': ep.get('PodcastEpisodeNumber', None),
            'channel': ch['PodcastChannelTitle'],
            'channel_id': str(ch['PodcastChannelId']),
            'formats': [{
                'format_id': 'audio',
                'url': ep['PodcastExtMediaUrl'],
                'vcodec': 'none',
            }]
        }
