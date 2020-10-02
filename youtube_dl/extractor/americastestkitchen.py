# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import (
    clean_html,
    int_or_none,
    js_to_json,
    try_get,
    unified_strdate,
)


class AmericasTestKitchenIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?americastestkitchen\.com/(?:episode|videos)/(?P<id>\d+)'
    _TESTS = [{
        'url': 'https://www.americastestkitchen.com/episode/582-weeknight-japanese-suppers',
        'md5': 'b861c3e365ac38ad319cfd509c30577f',
        'info_dict': {
            'id': '5b400b9ee338f922cb06450c',
            'title': 'Weeknight Japanese Suppers',
            'ext': 'mp4',
            'description': 'md5:3d0c1a44bb3b27607ce82652db25b4a8',
            'thumbnail': r're:^https?://',
            'timestamp': 1523664000,
            'upload_date': '20180414',
            'release_date': '20180414',
            'series': "America's Test Kitchen",
            'season_number': 18,
            'episode': 'Weeknight Japanese Suppers',
            'episode_number': 15,
        },
        'params': {
            'skip_download': True,
        },
    }, {
        'url': 'https://www.americastestkitchen.com/videos/3420-pan-seared-salmon',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)

        webpage = self._download_webpage(url, video_id)

        video_data = self._parse_json(
            self._search_regex(
                r'window\.__INITIAL_STATE__\s*=\s*({.+?})\s*;\s*</script>',
                webpage, 'initial context'),
            video_id, js_to_json)

        ep_data = try_get(
            video_data,
            (lambda x: x['episodeDetail']['content']['data'],
             lambda x: x['videoDetail']['content']['data']), dict)
        ep_meta = ep_data.get('full_video', {})

        zype_id = ep_data.get('zype_id') or ep_meta['zype_id']

        title = ep_data.get('title') or ep_meta.get('title')
        description = clean_html(ep_meta.get('episode_description') or ep_data.get(
            'description') or ep_meta.get('description'))
        thumbnail = try_get(ep_meta, lambda x: x['photo']['image_url'])
        release_date = unified_strdate(ep_data.get('aired_at'))

        season_number = int_or_none(ep_meta.get('season_number'))
        episode = ep_meta.get('title')
        episode_number = int_or_none(ep_meta.get('episode_number'))

        return {
            '_type': 'url_transparent',
            'url': 'https://player.zype.com/embed/%s.js?api_key=jZ9GUhRmxcPvX7M3SlfejB6Hle9jyHTdk2jVxG7wOHPLODgncEKVdPYBhuz9iWXQ' % zype_id,
            'ie_key': 'Zype',
            'title': title,
            'description': description,
            'thumbnail': thumbnail,
            'release_date': release_date,
            'series': "America's Test Kitchen",
            'season_number': season_number,
            'episode': episode,
            'episode_number': episode_number,
        }
