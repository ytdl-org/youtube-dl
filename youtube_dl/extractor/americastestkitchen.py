# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import (
    clean_html,
    int_or_none,
    try_get,
    unified_strdate,
)


class AmericasTestKitchenIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?americastestkitchen\.com/(?:episode|videos)/(?P<id>\d+)'
    _TESTS = [{
        'url': 'https://www.americastestkitchen.com/episode/548-summer-dinner-party',
        'md5': 'b861c3e365ac38ad319cfd509c30577f',
        'info_dict': {
            'id': '1_5g5zua6e',
            'title': 'Summer Dinner Party',
            'ext': 'mp4',
            'description': 'md5:858d986e73a4826979b6a5d9f8f6a1ec',
            'thumbnail': r're:^https?://.*\.jpg',
            'timestamp': 1497285541,
            'upload_date': '20170612',
            'uploader_id': 'roger.metcalf@americastestkitchen.com',
            'release_date': '20170617',
            'series': "America's Test Kitchen",
            'season_number': 17,
            'episode': 'Summer Dinner Party',
            'episode_number': 24,
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

        partner_id = self._search_regex(
            r'src=["\'](?:https?:)?//(?:[^/]+\.)kaltura\.com/(?:[^/]+/)*(?:p|partner_id)/(\d+)',
            webpage, 'kaltura partner id')

        video_data = self._parse_json(
            self._search_regex(
                r'window\.__INITIAL_STATE__\s*=\s*({.+?})\s*;\s*</script>',
                webpage, 'initial context'),
            video_id)

        ep_data = try_get(
            video_data,
            (lambda x: x['episodeDetail']['content']['data'],
             lambda x: x['videoDetail']['content']['data']), dict)
        ep_meta = ep_data.get('full_video', {})
        external_id = ep_data.get('external_id') or ep_meta['external_id']

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
            'url': 'kaltura:%s:%s' % (partner_id, external_id),
            'ie_key': 'Kaltura',
            'title': title,
            'description': description,
            'thumbnail': thumbnail,
            'release_date': release_date,
            'series': "America's Test Kitchen",
            'season_number': season_number,
            'episode': episode,
            'episode_number': episode_number,
        }
