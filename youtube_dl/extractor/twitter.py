from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..compat import compat_urllib_request
from ..utils import (
    float_or_none,
    unescapeHTML,
)


class TwitterCardIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?twitter\.com/i/cards/tfw/v1/(?P<id>\d+)'
    _TEST = {
        'url': 'https://twitter.com/i/cards/tfw/v1/560070183650213889',
        'md5': 'a74f50b310c83170319ba16de6955192',
        'info_dict': {
            'id': '560070183650213889',
            'ext': 'mp4',
            'title': 'TwitterCard',
            'thumbnail': 're:^https?://.*\.jpg$',
            'duration': 30.033,
        },
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)

        # Different formats served for different User-Agents
        USER_AGENTS = [
            'Mozilla/5.0 (X11; Linux x86_64; rv:10.0) Gecko/20150101 Firefox/20.0 (Chrome)',  # mp4
            'Mozilla/5.0 (Windows NT 5.2; WOW64; rv:38.0) Gecko/20100101 Firefox/38.0',  # webm
        ]

        config = None
        formats = []
        for user_agent in USER_AGENTS:
            request = compat_urllib_request.Request(url)
            request.add_header('User-Agent', user_agent)
            webpage = self._download_webpage(request, video_id)

            config = self._parse_json(
                unescapeHTML(self._search_regex(
                    r'data-player-config="([^"]+)"', webpage, 'data player config')),
                video_id)

            video_url = config['playlist'][0]['source']

            f = {
                'url': video_url,
            }

            m = re.search(r'/(?P<width>\d+)x(?P<height>\d+)/', video_url)
            if m:
                f.update({
                    'width': int(m.group('width')),
                    'height': int(m.group('height')),
                })
            formats.append(f)
        self._sort_formats(formats)

        thumbnail = config.get('posterImageUrl')
        duration = float_or_none(config.get('duration'))

        return {
            'id': video_id,
            'title': 'TwitterCard',
            'thumbnail': thumbnail,
            'duration': duration,
            'formats': formats,
        }
