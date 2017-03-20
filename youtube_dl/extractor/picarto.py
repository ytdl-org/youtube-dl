# coding: utf-8
from __future__ import unicode_literals

import re
import time

from .common import InfoExtractor
from ..utils import ExtractorError
from ..compat import compat_str


class PicartoIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?picarto\.tv/(?P<id>[a-zA-Z0-9]+)'
    _TEST = {
        'url': 'https://picarto.tv/setz',
        'info_dict': {
            'id': 'Setz',
            'ext': 'mp4',
            'title': 're:^Setz [0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}$',  # match self._live_title
            'timestamp': int,
            'is_live': True
        },
        'params': {
            # Livestream
            'skip_download': True
        }
    }
    _PLACESTREAM_REGEX = r'''(?x)
                             placeStream\(
                                "(?P<channel>[a-zA-Z0-9]+)",
                                (?P<player_id>\d+),
                                (?P<product>\d+),
                                (?P<offline_image>\d+),
                                (?P<online>\d+),
                                "(?P<token>.+?)",
                                "(?P<tech>.+?)",
                                (?P<viewer>\d+)\ *
                            \);
                        '''.replace(r',', r',\ *')

    def _real_extract(self, url):
        url_channel_id = self._match_id(url)
        stream_page = self._download_webpage('https://picarto.tv/' + url_channel_id, url_channel_id, note="Downloading channel page")

        # Handle nonexistent channels
        if 'This channel does not exist.' in stream_page:
            raise ExtractorError("Channel does not exist", expected=True)

        # Grab all relevant stream info
        placestream_m = re.search(self._PLACESTREAM_REGEX, stream_page)

        if not placestream_m:
            raise ExtractorError("Unable to fetch channel info")
        elif int(placestream_m.group('online')) == 0:
            raise ExtractorError("Stream is offline", expected=True)

        channel_id = placestream_m.group('channel')
        player_id = placestream_m.group('player_id')
        token = placestream_m.group('token')

        # Ask for stream host
        post_body = ('loadbalancinginfo=' + channel_id).encode('utf-8')
        load_balancing_info = self._download_webpage('https://picarto.tv/process/channel', channel_id, data=post_body, note="Fetching load balancer info")

        if not load_balancing_info or load_balancing_info in ('FULL', 'failedGetIP'):
            raise ExtractorError("Unable to get stream")

        timestamp = time.time()

        video_url = "https://%s-%s/mp4/%s.mp4?token=%s&ts=%s" % (player_id, load_balancing_info,
                                                                 channel_id, token, compat_str(int(timestamp * 1000)))

        return {
            'id': channel_id,
            'url': video_url,
            'ext': 'mp4',
            'title': self._live_title(channel_id),
            'timestamp': int(timestamp),
            'is_live': True
        }
