# coding: utf-8
from __future__ import unicode_literals

import re

from .theplatform import ThePlatformFeedIE
from ..utils import int_or_none


class CorusIE(ThePlatformFeedIE):
    _VALID_URL = r'https?://(?:www\.)?(?P<domain>(?:globaltv|etcanada)\.com|(?:hgtv|foodnetwork|slice)\.ca)/(?:video/|(?:[^/]+/)+(?:videos/[a-z0-9-]+-|video\.html\?.*?\bv=))(?P<id>\d+)'
    _TESTS = [{
        'url': 'http://www.hgtv.ca/shows/bryan-inc/videos/movie-night-popcorn-with-bryan-870923331648/',
        'md5': '05dcbca777bf1e58c2acbb57168ad3a6',
        'info_dict': {
            'id': '870923331648',
            'ext': 'mp4',
            'title': 'Movie Night Popcorn with Bryan',
            'description': 'Bryan whips up homemade popcorn, the old fashion way for Jojo and Lincoln.',
            'uploader': 'SHWM-NEW',
            'upload_date': '20170206',
            'timestamp': 1486392197,
        },
    }, {
        'url': 'http://www.foodnetwork.ca/shows/chopped/video/episode/chocolate-obsession/video.html?v=872683587753',
        'only_matching': True,
    }, {
        'url': 'http://etcanada.com/video/873675331955/meet-the-survivor-game-changers-castaways-part-2/',
        'only_matching': True,
    }]

    _TP_FEEDS = {
        'globaltv': {
            'feed_id': 'ChQqrem0lNUp',
            'account_id': 2269680845,
        },
        'etcanada': {
            'feed_id': 'ChQqrem0lNUp',
            'account_id': 2269680845,
        },
        'hgtv': {
            'feed_id': 'L0BMHXi2no43',
            'account_id': 2414428465,
        },
        'foodnetwork': {
            'feed_id': 'ukK8o58zbRmJ',
            'account_id': 2414429569,
        },
        'slice': {
            'feed_id': '5tUJLgV2YNJ5',
            'account_id': 2414427935,
        },
    }

    def _real_extract(self, url):
        domain, video_id = re.match(self._VALID_URL, url).groups()
        feed_info = self._TP_FEEDS[domain.split('.')[0]]
        return self._extract_feed_info('dtjsEC', feed_info['feed_id'], 'byId=' + video_id, video_id, lambda e: {
            'episode_number': int_or_none(e.get('pl1$episode')),
            'season_number': int_or_none(e.get('pl1$season')),
            'series': e.get('pl1$show'),
        }, {
            'HLS': {
                'manifest': 'm3u',
            },
            'DesktopHLS Default': {
                'manifest': 'm3u',
            },
            'MP4 MBR': {
                'manifest': 'm3u',
            },
        }, feed_info['account_id'])
