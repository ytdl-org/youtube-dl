from __future__ import unicode_literals

import json

from .common import InfoExtractor
from ..utils import (
    parse_iso8601,
    compat_urllib_parse,
    parse_age_limit,
    int_or_none,
)


class OpenFilmIE(InfoExtractor):
    _VALID_URL = r'http://(?:www\.)openfilm\.com/videos/(?P<id>.+)'
    _TEST = {
        'url': 'http://www.openfilm.com/videos/human-resources-remastered',
        'md5': '42bcd88c2f3ec13b65edf0f8ad1cac37',
        'info_dict': {
            'id': '32736',
            'display_id': 'human-resources-remastered',
            'ext': 'mp4',
            'title': 'Human Resources (Remastered)',
            'description': 'Social Engineering in the 20th Century.',
            'thumbnail': 're:^https?://.*\.jpg$',
            'duration': 7164,
            'timestamp': 1334756988,
            'upload_date': '20120418',
            'uploader_id': '41117',
            'view_count': int,
            'age_limit': 0,
        },
    }

    def _real_extract(self, url):
        display_id = self._match_id(url)

        webpage = self._download_webpage(url, display_id)

        player = compat_urllib_parse.unquote_plus(
            self._og_search_video_url(webpage))

        video = json.loads(self._search_regex(
            r'\bp=({.+?})(?:&|$)', player, 'video JSON'))

        video_url = '%s1.mp4' % video['location']
        video_id = video.get('video_id')
        display_id = video.get('alias') or display_id
        title = video.get('title')
        description = video.get('description')
        thumbnail = video.get('main_thumb')
        duration = int_or_none(video.get('duration'))
        timestamp = parse_iso8601(video.get('dt_published'), ' ')
        uploader_id = video.get('user_id')
        view_count = int_or_none(video.get('views_count'))
        age_limit = parse_age_limit(video.get('age_limit'))

        return {
            'id': video_id,
            'display_id': display_id,
            'url': video_url,
            'title': title,
            'description': description,
            'thumbnail': thumbnail,
            'duration': duration,
            'timestamp': timestamp,
            'uploader_id': uploader_id,
            'view_count': view_count,
            'age_limit': age_limit,
        }
