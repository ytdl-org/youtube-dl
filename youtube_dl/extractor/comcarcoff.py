# encoding: utf-8
from __future__ import unicode_literals

import json

from .common import InfoExtractor
from ..utils import parse_iso8601


class ComCarCoffIE(InfoExtractor):
    _VALID_URL = r'http://(?:www\.)?comediansincarsgettingcoffee\.com/(?P<id>[a-z0-9\-]*)'
    _TESTS = [{
        'url': 'http://comediansincarsgettingcoffee.com/miranda-sings-happy-thanksgiving-miranda/',
        'info_dict': {
            'id': 'miranda-sings-happy-thanksgiving-miranda',
            'ext': 'mp4',
            'upload_date': '20141127',
            'timestamp': 1417107600,
            'title': 'Happy Thanksgiving Miranda',
            'description': 'Jerry Seinfeld and his special guest Miranda Sings cruise around town in search of coffee, complaining and apologizing along the way.',
            'thumbnail': 'http://ccc.crackle.com/images/s5e4_thumb.jpg',
        },
        'params': {
            'skip_download': 'requires ffmpeg',
        }
    }]

    def _real_extract(self, url):
        display_id = self._match_id(url)
        if not display_id:
            display_id = 'comediansincarsgettingcoffee.com'
        webpage = self._download_webpage(url, display_id)

        full_data = json.loads(self._search_regex(
            r'<script type="application/json" id="videoData">(?P<json>.+?)</script>',
            webpage, 'full data json'))

        video_id = full_data['activeVideo']['video']
        video_data = full_data.get('videos', {}).get(video_id) or full_data['singleshots'][video_id]
        thumbnails = [{
            'url': video_data['images']['thumb'],
        }, {
            'url': video_data['images']['poster'],
        }]
        formats = self._extract_m3u8_formats(
            video_data['mediaUrl'], video_id, ext='mp4')

        return {
            'id': video_id,
            'display_id': display_id,
            'title': video_data['title'],
            'description': video_data.get('description'),
            'timestamp': parse_iso8601(video_data.get('pubDate')),
            'thumbnails': thumbnails,
            'formats': formats,
            'webpage_url': 'http://comediansincarsgettingcoffee.com/%s' % (video_data.get('urlSlug', video_data.get('slug'))),
        }
