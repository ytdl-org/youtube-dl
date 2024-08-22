from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import urlencode_postdata, try_get


class SexuIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?sexu\.com/(?P<id>\d+)'
    _TEST = {
        'url': 'http://sexu.com/961791/',
        'md5': 'ff615aca9691053c94f8f10d96cd7884',
        'info_dict': {
            'id': '961791',
            'ext': 'mp4',
            'title': 'md5:4d05a19a5fc049a63dbbaf05fb71d91b',
            'description': 'md5:6c7e471f9ac9bc326a9ad27be409f617',
            'categories': list,  # NSFW
            'thumbnail': r're:https?://.*\.jpg$',
            'age_limit': 18,
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        apiresponse = self._download_json(
            'https://sexu.com/api/video-info',
            video_id, data=urlencode_postdata({'videoId': video_id}))

        formats = [{
            'url': source.get('src'),
            'format_id': source.get('type'),
            'height': int(self._search_regex(
                r'^(\d+)[pP]', source.get('quality', ''), 'height',
                default=None)),
        } for source in try_get(apiresponse, lambda x: x['sources'])]
        self._sort_formats(formats)

        title = self._og_search_property('title', webpage)

        description = self._html_search_meta(
            'description', webpage, 'description')

        thumbnail = self._og_search_property('image', webpage)

        categories = re.findall(
            r'(?s)<a[^>]+class=[\'"]player-tags__item[^>]*>([^<]+)</a>', webpage)

        return {
            'id': video_id,
            'title': title,
            'description': description,
            'thumbnail': thumbnail,
            'categories': categories,
            'formats': formats,
            'age_limit': 18,
        }
