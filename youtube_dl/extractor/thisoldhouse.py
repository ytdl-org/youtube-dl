# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..compat import compat_str
from ..utils import (
    try_get,
    int_or_none
)


class ThisOldHouseIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?thisoldhouse\.com/(?:watch|how-to|tv-episode)/(?P<id>[^/?#]+)'
    _TESTS = [{
        'url': 'https://www.thisoldhouse.com/how-to/how-to-build-storage-bench',
        'md5': '568acf9ca25a639f0c4ff905826b662f',
        'info_dict': {
            'id': '2REGtUDQ',
            'ext': 'mp4',
            'title': 'How to Build a Storage Bench',
            'description': 'In the workshop, Tom Silva and Kevin O\'Connor build a storage bench for an entryway.',
            'timestamp': 1442548800,
            'upload_date': '20150918',
        }
    }, {
        'url': 'https://www.thisoldhouse.com/watch/taking-modern-back-to-future-brookline-mid-century-modern-house',
        'md5': '5bff4b17e959527066efba9371bb81ba',
        'info_dict': {
            'id': '8WrwQuEr',
            'ext': 'mp4',
            'title': 'Taking Modern Back to the Future | Brookline Mid-Century Modern House',
            'description': 'After months of hard work, the lackluster mid-century box is a modern marvel once again. Kevin, Tommy and Richard tour the home and review all the special features that went into this beautiful space Sunil and Neha can now call home.',
            'upload_date': '20190624',
            'timestamp': 1561397187,
            'season_number': 40,
            'episode_number': 26
        },
    }, {
        'url': 'https://www.thisoldhouse.com/watch/arlington-arts-crafts-arts-and-crafts-class-begins',
        'only_matching': True,
    }, {
        'url': 'https://www.thisoldhouse.com/tv-episode/ask-toh-shelf-rough-electric',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        display_id = self._match_id(url)
        webpage = self._download_webpage(url, display_id)
        video_id = self._search_regex(
            (r'data-mid=(["\'])(?P<id>(?:(?!\1).)+)\1',
             r'id=(["\'])inline-video-player-(?P<id>(?:(?!\1).)+)\1'),
            webpage, 'video id', default=None, group='id')
        if not video_id:
            drupal_settings = self._parse_json(self._search_regex(
                r'jQuery\.extend\(Drupal\.settings\s*,\s*({.+?})\);',
                webpage, 'drupal settings'), display_id)
            video_id = try_get(
                drupal_settings, lambda x: x['jwplatform']['video_id'],
                compat_str) or list(drupal_settings['comScore'])[0]

        series = self._search_regex(
            r'(?s)episode-breadcrumb.*?>.*?>(.*?)</a>', webpage,
            'series name', default=None)
        season_number = int_or_none(self._search_regex(
            r'Season (\d+);', webpage, 'season number',
            default=None))
        episode_number = int_or_none(self._search_regex(
            r'Season \d+;[\s\S]*Ep\.(\d+)', webpage, 'episode number',
            default=None))

        if series:
            series = series.replace(' TV', '')

        return {
            '_type': 'url_transparent',
            'id': video_id,
            'series': series,
            'season_number': season_number,
            'episode_number': episode_number,
            'url': 'jwplatform:' + video_id,
            'ie_key': 'JWPlatform',
        }
