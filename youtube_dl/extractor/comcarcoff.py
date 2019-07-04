# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..compat import compat_str
from ..utils import (
    int_or_none,
    parse_duration,
    parse_iso8601,
)


class ComCarCoffIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?comediansincarsgettingcoffee\.com/(?P<id>[a-z0-9\-]*)'
    _TESTS = [{
        'url': 'http://comediansincarsgettingcoffee.com/miranda-sings-happy-thanksgiving-miranda/',
        'info_dict': {
            'id': '2494164',
            'ext': 'mp4',
            'upload_date': '20141127',
            'timestamp': 1417107600,
            'duration': 1232,
            'title': 'Happy Thanksgiving Miranda',
            'description': 'Jerry Seinfeld and his special guest Miranda Sings cruise around town in search of coffee, complaining and apologizing along the way.',
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

        full_data = self._parse_json(
            self._search_regex(
                r'window\.app\s*=\s*({.+?});\n', webpage, 'full data json'),
            display_id)['videoData']

        display_id = full_data['activeVideo']['video']
        video_data = full_data.get('videos', {}).get(display_id) or full_data['singleshots'][display_id]

        video_id = compat_str(video_data['mediaId'])
        title = video_data['title']
        formats = self._extract_m3u8_formats(
            video_data['mediaUrl'], video_id, 'mp4')
        self._sort_formats(formats)

        thumbnails = [{
            'url': video_data['images']['thumb'],
        }, {
            'url': video_data['images']['poster'],
        }]

        timestamp = int_or_none(video_data.get('pubDateTime')) or parse_iso8601(
            video_data.get('pubDate'))
        duration = int_or_none(video_data.get('durationSeconds')) or parse_duration(
            video_data.get('duration'))

        return {
            'id': video_id,
            'display_id': display_id,
            'title': title,
            'description': video_data.get('description'),
            'timestamp': timestamp,
            'duration': duration,
            'thumbnails': thumbnails,
            'formats': formats,
            'season_number': int_or_none(video_data.get('season')),
            'episode_number': int_or_none(video_data.get('episode')),
            'webpage_url': 'http://comediansincarsgettingcoffee.com/%s' % (video_data.get('urlSlug', video_data.get('slug'))),
        }
