# coding: utf-8
from __future__ import unicode_literals

import json
import codecs
from datetime import datetime
from functools import reduce

from .common import InfoExtractor
from ..utils import ExtractorError


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

        # Extracting JSON from webpage
        initial_state_str = self._html_search_regex(r'window.__INITIAL_STATE__ = JSON.parse\("([^;].*)"\);', webpage, 'url')
        json_state = json.loads(codecs.decode(initial_state_str, 'unicode-escape'))

        # Parsing metadata
        entities = json_state.get('@@entities', {})
        deviation = entities.get('deviation', {}).get(video_id, {})
        media_types = deviation.get('media', {}).get('types', [])
        video_types = list(filter(lambda element: element.get('t') == 'video', media_types))
        video_type = reduce(lambda x, y: y if x.get('w', 0) < y.get('w', 0) else x, video_types)

        if not deviation.get('isVideo', False) or not video_type:
            raise ExtractorError('no video info found in requested element', expected=True)

        upload_date = datetime.fromisoformat(deviation.get('publishedTime')[:-5]) if deviation.get('publishedTime') else None
        deviation_ext = entities.get('deviationExtended', {}).get(video_id, {})
        tags = list(map(lambda tag: tag.get('name'), deviation_ext.get('tags', [])))

        return {
            'id': f"{deviation.get('deviationId')}",
            'title': deviation.get('title'),
            'description': deviation_ext.get('descriptionText', {}).get('html', {}).get('markup'),
            'uploader': self._search_regex(self._VALID_URL, url, 'uploader', group=1, fatal=False),
            'url': video_type.get('b'),
            'thumbnail': deviation.get('media', {}).get('baseUri'),
            'upload_date': upload_date.strftime("%Y%m%d") if upload_date is not None else None,
            'uploader_id': deviation.get('author'),
            'view_count': deviation.get('stats', {}).get('views'),
            'height': video_type.get('h'),
            'width': video_type.get('w'),
            'filesize': deviation_ext.get('originalFile', {}).get('filesize'),
            'tags': tags,
        }
