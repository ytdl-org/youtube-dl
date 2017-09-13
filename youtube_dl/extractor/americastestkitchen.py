# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor


class AmericasTestKitchenIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?americastestkitchen\.com/episode/(?P<id>\d+)'
    _TESTS = [{
        'url':
        'https://www.americastestkitchen.com/episode/548-summer-dinner-party',
        'md5': 'b861c3e365ac38ad319cfd509c30577f',
        'info_dict': {
            'id': '1_5g5zua6e',
            'title': 'atk_s17_e24.mp4',
            'ext': 'mp4',
            'description': '<p>Host Julia Collin Davison goes into the test kitchen with test cook Dan Souza to learn how to make the ultimate Grill-Roasted Beef Tenderloin. Next, equipment expert Adam Ried reviews gas grills in the Equipment Corner. Then, gadget guru Lisa McManus uncovers the best quirky gadgets. Finally, test cook Erin McMurrer shows host Bridget Lancaster how to make an elegant Pear-Walnut Upside-Down Cake.</p>',
            'timestamp': 1497285541,
            'upload_date': '20170612',
            'uploader_id': 'roger.metcalf@americastestkitchen.com',
            'release_date': '2017-06-17',
            'thumbnail': 'http://d3cizcpymoenau.cloudfront.net/images/35973/e24-tenderloin-16.jpg',
            'episode_number': 24,
            'episode': 'Summer Dinner Party',
            'episode_id': '548-summer-dinner-party',
            'season_number': 17
        },
        'params': {
            # m3u8 download
            'skip_download': True,
        },
    }, {
        'url':
        'https://www.americastestkitchen.com/episode/546-a-spanish-affair',
        'only_matching':
        True,
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        partner_id = self._search_regex(
            r'partner_id/(?P<partner_id>\d+)',
            webpage,
            'partner_id',
            group='partner_id')

        video_data = self._parse_json(
            self._search_regex(
                r'window\.__INITIAL_STATE__\s*=\s*({.+?});\s*</script>',
                webpage, 'initial context'),
            video_id)

        episode_data = video_data['episodeDetail']['content']['data']
        episode_content_meta = episode_data['full_video']
        external_id = episode_content_meta['external_id']

        # photo data
        photo_data = episode_content_meta.get('photo')
        thumbnail = photo_data.get('image_url') if photo_data else None

        # meta
        release_date = episode_data.get('aired_at')
        description = episode_content_meta.get('description')
        episode_number = int(episode_content_meta.get('episode_number'))
        episode = episode_content_meta.get('title')
        episode_id = episode_content_meta.get('episode_slug')
        season_number = int(episode_content_meta.get('season_number'))

        return {
            '_type': 'url_transparent',
            'url': 'kaltura:%s:%s' % (partner_id, external_id),
            'ie_key': 'Kaltura',
            'id': video_id,
            'release_date': release_date,
            'thumbnail': thumbnail,
            'description': description,
            'episode_number': episode_number,
            'episode': episode,
            'episode_id': episode_id,
            'season_number': season_number
        }
