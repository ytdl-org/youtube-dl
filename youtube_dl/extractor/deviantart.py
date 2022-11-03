# coding: utf-8
from __future__ import unicode_literals

import json
import codecs
from datetime import datetime
from functools import reduce

from .common import InfoExtractor


class DeviantArtIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?deviantart\.com/(?P<uploader>[a-zA-Z0-9]+)/art/([a-zA-Z0-9-]+)-(?P<id>\d+)'
    _TEST = {
        'url': 'https://www.deviantart.com/spacialcube/art/animated-Caramelldansen-935129468',
        'md5': 'TODO: md5 sum of the first 10241 bytes of the video file (use --test)',
        'info_dict': {
            'id': '935129468',
            'ext': 'mp4',
            'title': '[animated] Caramelldansen',
            'thumbnail': r're:^https?://.*\.jpg$',
            # TODO more properties, either as:
            # * A value
            # * MD5 checksum; start the string with md5:
            # * A regular expression; start the string with re:
            # * Any Python type (for example int or float)
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)
        initial_state_str = self._html_search_regex(r'window.__INITIAL_STATE__ = JSON.parse\("([^;].*)"\);', webpage, 'url')
        json_state = json.loads(codecs.decode(initial_state_str, 'unicode-escape'))
        metadata = json_state.get('@@entities', {}).get('deviation', {}).get(video_id, {})
        upload_date = datetime.fromisoformat(metadata.get('publishedTime')[:-5]) if metadata.get('publishedTime') else None
        media_types = metadata.get('media', {}).get('types', [])
        video_types = list(filter(lambda element: element.get('t') == 'video', media_types))
        video_type = reduce(lambda x, y: y if x.get('w', 0) < y.get('w', 0) else x, video_types)

        return {
            'id': metadata.get('deviationId'),
            'title': metadata.get('title'),
            'description': self._og_search_description(webpage),
            'uploader': self._search_regex(self._VALID_URL, url, 'uploader', group=1, fatal=False),
            'url': video_type.get('b'),
            'thumbnail': metadata.get('media', {}).get('baseUri'),
            'upload_date': upload_date.strftime("%Y%m%d") if upload_date is not None else None,
            'uploader_id': metadata.get('author'),
            'view_count': metadata.get('stats', {}).get('views'),
        }
