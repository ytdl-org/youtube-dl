from __future__ import unicode_literals

import re
import json

from .common import InfoExtractor
from ..utils import int_or_none


class VideoBamIE(InfoExtractor):
    _VALID_URL = r'http://(?:www\.)?videobam\.com/(?:videos/download/)?(?P<id>[a-zA-Z]+)'

    _TESTS = [
        {
            'url': 'http://videobam.com/OiJQM',
            'md5': 'db471f27763a531f10416a0c58b5a1e0',
            'info_dict': {
                'id': 'OiJQM',
                'ext': 'mp4',
                'title': 'Is Alcohol Worse Than Ecstasy?',
                'description': 'md5:d25b96151515c91debc42bfbb3eb2683',
                'uploader': 'frihetsvinge',
            },
        },
        {
            'url': 'http://videobam.com/pqLvq',
            'md5': 'd9a565b5379a99126ef94e1d7f9a383e',
            'note': 'HD video',
            'info_dict': {
                'id': 'pqLvq',
                'ext': 'mp4',
                'title': '_',
            }
        },
    ]

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')

        page = self._download_webpage('http://videobam.com/%s' % video_id, video_id, 'Downloading page')

        formats = []

        for preference, format_id in enumerate(['low', 'high']):
            mobj = re.search(r"%s: '(?P<url>[^']+)'" % format_id, page)
            if not mobj:
                continue
            formats.append({
                'url': mobj.group('url'),
                'ext': 'mp4',
                'format_id': format_id,
                'preference': preference,
            })

        if not formats:
            player_config = json.loads(self._html_search_regex(r'var player_config = ({.+?});', page, 'player config'))
            formats = [{
                'url': item['url'],
                'ext': 'mp4',
            } for item in player_config['playlist'] if 'autoPlay' in item]

        self._sort_formats(formats)

        title = self._og_search_title(page, default='_', fatal=False)
        description = self._og_search_description(page, default=None)
        thumbnail = self._og_search_thumbnail(page)
        uploader = self._html_search_regex(r'Upload by ([^<]+)</a>', page, 'uploader', fatal=False, default=None)
        view_count = int_or_none(
            self._html_search_regex(r'<strong>Views:</strong> (\d+) ', page, 'view count', fatal=False))

        return {
            'id': video_id,
            'title': title,
            'description': description,
            'thumbnail': thumbnail,
            'uploader': uploader,
            'view_count': view_count,
            'formats': formats,
            'age_limit': 18,
        }
