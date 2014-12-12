# encoding: utf-8
import re
import json

from .common import InfoExtractor
from ..utils import (
    unified_strdate,
)

class ComCarCoffIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?comediansincarsgettingcoffee\.com/(?P<id>[a-z0-9\-]+)/?'
    _TESTS = [
        {
            'url': 'http://comediansincarsgettingcoffee.com/miranda-sings-happy-thanksgiving-miranda/',
            'info_dict': {
                'id': 'miranda-sings-happy-thanksgiving-miranda',
                'upload_date': '20141127',
                'title': 'Happy Thanksgiving Miranda',
                'description': 'Jerry Seinfeld and his special guest Miranda Sings cruise around town in search of coffee, complaining and apologizing along the way.',
                'thumbnail': 'http://ccc.crackle.com/images/s5e4_thumb.jpg',
            },
        }
    ]

    def _real_extract(self, url):
        display_id = self._match_id(url)
        webpage = self._download_webpage(url, display_id)

        full_data = json.loads(self._search_regex(
            r'<script type="application/json" id="videoData">(?P<json>.+?)</script>',
            webpage, 'json'))

        video_id = full_data['activeVideo']['video']
        video_data = full_data['videos'][video_id]

        return {
            'id': video_id,
            'display_id': display_id,
            'title': video_data['title'],
            'description': video_data['description'],
            # XXX: the original datum is a full ISO timestamp... why convert it to a worse format?
            'upload_date': unified_strdate(video_data['pubDate']),
            'thumbnail': video_data['images']['thumb'],
            # XXX: what do we do with video_data['images']['poster']?
            'formats': self._extract_m3u8_formats(video_data['mediaUrl'], video_id),
        }
