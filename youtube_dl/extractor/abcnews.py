# coding: utf-8
from __future__ import unicode_literals

import re

from .amp import AMPIE


class AbcNewsVideoIE(AMPIE):
    IE_NAME = 'abcnews:video'
    _VALID_URL = r'''(?x)
                    https?://
                        (?:
                            abcnews\.go\.com/
                            (?:
                                [^/]+/video/(?P<display_id>[0-9a-z-]+)-|
                                video/embed\?.*?\bid=
                            )|
                            fivethirtyeight\.abcnews\.go\.com/video/embed/\d+/
                        )
                        (?P<id>\d+)
                    '''

    _TESTS = [{
        'url': 'http://abcnews.go.com/ThisWeek/video/week-exclusive-irans-foreign-minister-zarif-20411932',
        'info_dict': {
            'id': '20411932',
            'ext': 'mp4',
            'display_id': 'week-exclusive-irans-foreign-minister-zarif',
            'title': '\'This Week\' Exclusive: Iran\'s Foreign Minister Zarif',
            'description': 'George Stephanopoulos goes one-on-one with Iranian Foreign Minister Dr. Javad Zarif.',
            'duration': 180,
            'thumbnail': r're:^https?://.*\.jpg$',
            'timestamp': 1380454200,
            'upload_date': '20130929',
        },
        'params': {
            # m3u8 download
            'skip_download': True,
        },
    }, {
        'url': 'http://abcnews.go.com/video/embed?id=46979033',
        'only_matching': True,
    }, {
        'url': 'http://abcnews.go.com/2020/video/2020-husband-stands-teacher-jail-student-affairs-26119478',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        display_id = mobj.group('display_id')
        video_id = mobj.group('id')
        info_dict = self._extract_feed_info(
            'http://abcnews.go.com/video/itemfeed?id=%s' % video_id)
        info_dict.update({
            'id': video_id,
            'display_id': display_id,
        })
        return info_dict


class AbcNewsIE(AMPIE):
    IE_NAME = 'abcnews'
    _VALID_URL = r'https?://abcnews\.go\.com/(?:[^/]+/)+(?P<display_id>[0-9a-z-]+)/story\?id=(?P<id>\d+)'

    _TESTS = [{
        'url': 'https://abcnews.go.com/US/winter-storms-moving-us-snow-freezing-rain-flooding/story?id=75466370',
        'info_dict': {
            'id': '75466370',
            'ext': 'flv',
            'display_id': 'winter-storms-moving-us-snow-freezing-rain-flooding',
            'title': 'Winter storms moving across US with snow, freezing rain',
            'description': 'Two storms moved through the West this weekend with a funnel cloud reportedly being spotted in San Diego along with 1 to 2 feet of snow from California to Colorado.',
            'thumbnail': r're:^https?://.*\.jpg$',
            'upload_date': '20210125',
            'timestamp': 1611566880,
        },
        'add_ie': ['AbcNewsVideo'],
    }, {
        'url': 'http://abcnews.go.com/Entertainment/justin-timberlake-performs-stop-feeling-eurovision-2016/story?id=39125818',
        'info_dict': {
            'id': '39125818',
            'ext': 'mp4',
            'display_id': 'justin-timberlake-performs-stop-feeling-eurovision-2016',
            'title': 'Justin Timberlake Drops Hints For Secret Single',
            'description': 'Lara Spencer reports the buzziest stories of the day in "GMA" Pop News.',
            'upload_date': '20160505',
            'timestamp': 1462442280,
        },
        'params': {
            # m3u8 download
            'skip_download': True,
            # The embedded YouTube video is blocked due to copyright issues
            'playlist_items': '1',
        },
        'add_ie': ['AbcNewsVideo'],
    }, {
        'url': 'http://abcnews.go.com/Technology/exclusive-apple-ceo-tim-cook-iphone-cracking-software/story?id=37173343',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        display_id = mobj.group('display_id')
        video_id = mobj.group('id')

        webpage = self._download_webpage(url, video_id)
        feed_url = self._html_search_regex(r'"feed"\s*:\s*"(.*?)"', webpage, 'feed URL')

        info_dict = self._extract_feed_info(feed_url)
        info_dict.update({
            'id': video_id,
            'display_id': display_id,
        })
        return info_dict
