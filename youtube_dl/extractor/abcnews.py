# coding: utf-8
from __future__ import unicode_literals

import calendar
import re
import time

from .amp import AMPIE
from .common import InfoExtractor
from .youtube import YoutubeIE
from ..compat import compat_urlparse


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


class AbcNewsIE(InfoExtractor):
    IE_NAME = 'abcnews'
    _VALID_URL = r'https?://abcnews\.go\.com/(?:[^/]+/)+(?P<display_id>[0-9a-z-]+)/story\?id=(?P<id>\d+)'

    _TESTS = [{
        'url': 'http://abcnews.go.com/Blotter/News/dramatic-video-rare-death-job-america/story?id=10498713#.UIhwosWHLjY',
        'info_dict': {
            'id': '10505354',
            'ext': 'flv',
            'display_id': 'dramatic-video-rare-death-job-america',
            'title': 'Occupational Hazards',
            'description': 'Nightline investigates the dangers that lurk at various jobs.',
            'thumbnail': r're:^https?://.*\.jpg$',
            'upload_date': '20100428',
            'timestamp': 1272412800,
        },
        'add_ie': ['AbcNewsVideo'],
    }, {
        'url': 'http://abcnews.go.com/Entertainment/justin-timberlake-performs-stop-feeling-eurovision-2016/story?id=39125818',
        'info_dict': {
            'id': '38897857',
            'ext': 'mp4',
            'display_id': 'justin-timberlake-performs-stop-feeling-eurovision-2016',
            'title': 'Justin Timberlake Drops Hints For Secret Single',
            'description': 'Lara Spencer reports the buzziest stories of the day in "GMA" Pop News.',
            'upload_date': '20160515',
            'timestamp': 1463329500,
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
        video_url = self._search_regex(
            r'window\.abcnvideo\.url\s*=\s*"([^"]+)"', webpage, 'video URL')
        full_video_url = compat_urlparse.urljoin(url, video_url)

        youtube_url = YoutubeIE._extract_url(webpage)

        timestamp = None
        date_str = self._html_search_regex(
            r'<span[^>]+class="timestamp">([^<]+)</span>',
            webpage, 'timestamp', fatal=False)
        if date_str:
            tz_offset = 0
            if date_str.endswith(' ET'):  # Eastern Time
                tz_offset = -5
                date_str = date_str[:-3]
            date_formats = ['%b. %d, %Y', '%b %d, %Y, %I:%M %p']
            for date_format in date_formats:
                try:
                    timestamp = calendar.timegm(time.strptime(date_str.strip(), date_format))
                except ValueError:
                    continue
            if timestamp is not None:
                timestamp -= tz_offset * 3600

        entry = {
            '_type': 'url_transparent',
            'ie_key': AbcNewsVideoIE.ie_key(),
            'url': full_video_url,
            'id': video_id,
            'display_id': display_id,
            'timestamp': timestamp,
        }

        if youtube_url:
            entries = [entry, self.url_result(youtube_url, ie=YoutubeIE.ie_key())]
            return self.playlist_result(entries)

        return entry
