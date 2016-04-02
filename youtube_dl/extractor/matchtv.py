# coding: utf-8
from __future__ import unicode_literals

import random

from .common import InfoExtractor
from ..compat import compat_urllib_parse_urlencode
from ..utils import (
    sanitized_Request,
    xpath_text,
)


class MatchTVIE(InfoExtractor):
    _VALID_URL = r'https?://matchtv\.ru/?#live-player'
    _TEST = {
        'url': 'http://matchtv.ru/#live-player',
        'info_dict': {
            'id': 'matchtv-live',
            'ext': 'flv',
            'title': 're:^Матч ТВ - Прямой эфир \d{4}-\d{2}-\d{2} \d{2}:\d{2}$',
            'is_live': True,
        },
        'params': {
            'skip_download': True,
        },
    }

    def _real_extract(self, url):
        video_id = 'matchtv-live'
        request = sanitized_Request(
            'http://player.matchtv.ntvplus.tv/player/smil?%s' % compat_urllib_parse_urlencode({
                'ts': '',
                'quality': 'SD',
                'contentId': '561d2c0df7159b37178b4567',
                'sign': '',
                'includeHighlights': '0',
                'userId': '',
                'sessionId': random.randint(1, 1000000000),
                'contentType': 'channel',
                'timeShift': '0',
                'platform': 'portal',
            }),
            headers={
                'Referer': 'http://player.matchtv.ntvplus.tv/embed-player/NTVEmbedPlayer.swf',
            })
        video_url = self._download_json(request, video_id)['data']['videoUrl']
        f4m_url = xpath_text(self._download_xml(video_url, video_id), './to')
        formats = self._extract_f4m_formats(f4m_url, video_id)
        self._sort_formats(formats)
        return {
            'id': video_id,
            'title': self._live_title('Матч ТВ - Прямой эфир'),
            'is_live': True,
            'formats': formats,
        }
