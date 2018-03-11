from __future__ import unicode_literals

from .common import InfoExtractor
from .ooyala import OoyalaIE
from youtube_dl.utils import (
    ExtractorError,
)

import json
import re
import sys


class TastyTradeIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?tastytrade\.com/tt/(shows|daily_recaps)/[^/]+/episodes/(?P<id>[^/?#&]+)'

    _TESTS = [{
        'url': 'https://www.tastytrade.com/tt/shows/market-measures/episodes/correlation-in-short-volatility-06-28-2017',
        'info_dict': {
            'id': '8xZW5xYjE6aLXhPwseCpyIf50oQw69JM',
            'ext': 'mp4',
            'title': 'Correlation in Short Volatility',
            'description': '[Correlation](https://www.tastytrade.com/tt/learn/correlation) is always changing and positions can be more correlated than we suspect. We can even have...',
            'duration': 753.0,
            'upload_date': '20170628',
            'timestamp': 1498608000,
        },
        'params': {
            'skip_download': True,
        },
        'add_ie': ['Ooyala'],
    }, {
        'url': 'https://www.tastytrade.com/tt/shows/daily-dose/episodes/daily-dose-06-30-2017',
        'only_matching': True,
    }, {
        'url': 'https://www.tastytrade.com/tt/daily_recaps/2018-03-09/episodes/soybeans-corn-its-planting-time-03-09-2018',
        'info_dict': {
            'id': 'lud3BtZTE6vnRdolxKRlwNoZQvb3z_LT',
            'ext': 'mp4',
            'title': 'Soybeans & Corn: It\'s Planting Time',
            'description': 'md5:a523504b1227de1b81faeba2876a6d23',
        },
        'params': {
            'skip_download': True,
        },
        'add_ie': ['Ooyala'],
    }]

    def _real_extract(self, url):
        display_id = self._match_id(url)
        webpage = self._download_webpage(url, display_id)

        ooyala_code = self._search_regex(
            r'data-media-id=(["\'])(?P<code>(?:(?!\1).)+)\1',
            webpage, 'ooyala code', group='code')

        info = {'id': None, 'title': None, 'description': None}

        try:
            info = self._search_json_ld(webpage, display_id, fatal=False)
        except ExtractorError as ex:
            json_string_match = re.search(
                r'var episodeData = \$.parseJSON\("(?P<episode_json>.*)"\)', webpage, 0)

            if (json_string_match):
                escaped_json_string = json_string_match.group('episode_json')

                if sys.version_info[0] >= 3:
                    unescaped_json_string = bytes(
                        escaped_json_string, "utf-8").decode('unicode_escape')
                else:
                    unescaped_json_string = escaped_json_string.decode(
                        'string_escape')
                metadata = json.loads(unescaped_json_string)
                info = {
                    'id': metadata.get('mediaId'),
                    'title': metadata.get('title'),
                    'description': metadata.get('description')
                }

        info.update({
            '_type': 'url_transparent',
            'ie_key': OoyalaIE.ie_key(),
            'url': 'ooyala:%s' % ooyala_code,
            'display_id': display_id,
        })
        return info
