# coding: utf-8
from __future__ import unicode_literals

import json
import re

from .common import InfoExtractor
from ..utils import (
    clean_html,
    int_or_none,
    try_get,
    unified_strdate,
    unified_timestamp,
)


class AmericasTestKitchenIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?(?:americastestkitchen|cooks(?:country|illustrated))\.com/(?P<resource_type>episode|videos)/(?P<id>\d+)'
    _TESTS = [{
        'url': 'https://www.americastestkitchen.com/episode/582-weeknight-japanese-suppers',
        'md5': 'b861c3e365ac38ad319cfd509c30577f',
        'info_dict': {
            'id': '5b400b9ee338f922cb06450c',
            'title': 'Japanese Suppers',
            'ext': 'mp4',
            'description': 'md5:64e606bfee910627efc4b5f050de92b3',
            'thumbnail': r're:^https?://',
            'timestamp': 1523318400,
            'upload_date': '20180410',
            'release_date': '20180410',
            'series': "America's Test Kitchen",
            'season_number': 18,
            'episode': 'Japanese Suppers',
            'episode_number': 15,
        },
        'params': {
            'skip_download': True,
        },
    }, {
        # Metadata parsing behaves differently for newer episodes (705) as opposed to older episodes (582 above)
        'url': 'https://www.americastestkitchen.com/episode/705-simple-chicken-dinner',
        'md5': '06451608c57651e985a498e69cec17e5',
        'info_dict': {
            'id': '5fbe8c61bda2010001c6763b',
            'title': 'Simple Chicken Dinner',
            'ext': 'mp4',
            'description': 'md5:eb68737cc2fd4c26ca7db30139d109e7',
            'thumbnail': r're:^https?://',
            'timestamp': 1610755200,
            'upload_date': '20210116',
            'release_date': '20210116',
            'series': "America's Test Kitchen",
            'season_number': 21,
            'episode': 'Simple Chicken Dinner',
            'episode_number': 3,
        },
        'params': {
            'skip_download': True,
        },
    }, {
        'url': 'https://www.americastestkitchen.com/videos/3420-pan-seared-salmon',
        'only_matching': True,
    }, {
        'url': 'https://www.cookscountry.com/episode/564-when-only-chocolate-will-do',
        'only_matching': True,
    }, {
        'url': 'https://www.cooksillustrated.com/videos/4478-beef-wellington',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        resource_type, video_id = re.match(self._VALID_URL, url).groups()
        is_episode = resource_type == 'episode'
        if is_episode:
            resource_type = 'episodes'

        resource = self._download_json(
            'https://www.americastestkitchen.com/api/v6/%s/%s' % (resource_type, video_id), video_id)
        video = resource['video'] if is_episode else resource
        episode = resource if is_episode else resource.get('episode') or {}

        return {
            '_type': 'url_transparent',
            'url': 'https://player.zype.com/embed/%s.js?api_key=jZ9GUhRmxcPvX7M3SlfejB6Hle9jyHTdk2jVxG7wOHPLODgncEKVdPYBhuz9iWXQ' % video['zypeId'],
            'ie_key': 'Zype',
            'description': clean_html(video.get('description')),
            'timestamp': unified_timestamp(video.get('publishDate')),
            'release_date': unified_strdate(video.get('publishDate')),
            'episode_number': int_or_none(episode.get('number')),
            'season_number': int_or_none(episode.get('season')),
            'series': try_get(episode, lambda x: x['show']['title']),
            'episode': episode.get('title'),
        }


class AmericasTestKitchenPlaylistIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?americastestkitchen\.com/episodes/browse/season\_(?P<id>\d+)'
    _TESTS = [{
        # Single-digit season
        'url': 'https://www.americastestkitchen.com/episodes/browse/season_1',
        'info_dict': {
            'id': 'season-1',
            'title': 'Season 1',
        },
        'playlist_count': 13,
    }, {
        # Multi-digit season
        'url': 'https://www.americastestkitchen.com/episodes/browse/season_20',
        'info_dict': {
            'id': 'season-20',
            'title': 'Season 20',
        },
        'playlist_count': 26,
    }]

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        season = mobj.group('id')

        data = {
            'requests': [
                {
                    'indexName': 'everest_search_atk_season_desc_production',
                    'params': 'filters=search_document_klass%3Aepisode%20AND%20search_site_list%3Aatk%20AND%20search_show_slug%3Aatk%20&enableRules=false&hitsPerPage=30&maxValuesPerFacet=21&page=0&facets=%5B%22search_season_list%22%5D&tagFilters=&facetFilters=%5B%5B%22search_season_list%3ASeason%20' + season + '%22%5D%5D'

                }
            ]
        }

        # ATK uses a third-party provider to list the episodes for each season
        # The data to provide it must be sent with content-type=application/x-www-form-urlencoded
        # But the endpoint actually just wants JSON
        season_search = self._download_json(
            'https://y1fnzxui30-dsn.algolia.net/1/indexes/*/queries?x-algolia-agent=Algolia%20for%20JavaScript%20(3.35.1)%3B%20Browser%3B%20JS%20Helper%20(3.1.1)%3B%20react%20(16.13.1)%3B%20react-instantsearch%20(6.5.0)&x-algolia-application-id=Y1FNZXUI30&x-algolia-api-key=8d504d0099ed27c1b73708d22871d805',
            season, data=json.dumps(data), headers={
                'Origin': 'https://www.americastestkitchen.com',
                'Content-Type': 'application/x-www-form-urlencoded'
            })

        episode_paths = season_search['results'][0]['hits']

        entries = [
            self.url_result('https://www.americastestkitchen.com' + episode['search_url'], 'AmericasTestKitchen', episode['objectID'])
            for episode in episode_paths
        ]

        return {
            '_type': 'playlist',
            'id': 'season-%s' % season,
            'title': 'Season %s' % season,
            'entries': entries,
        }
