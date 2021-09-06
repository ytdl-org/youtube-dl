# coding: utf-8
from __future__ import unicode_literals
import re

from ..utils import unified_timestamp, parse_duration
from .common import InfoExtractor


class SnapchatIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?story.snapchat\.com/o/(?P<id>\w+)'
    _TEST = {
        'url': 'https://story.snapchat.com/o/W7_EDlXWTBiXAEEniNoMPwAAYuz9_1mcdex8MAXndPyIOAXndPyFyAO1OAA',
        'md5': 'ab1900981cadcd955aae32a526096cbd',
        'info_dict': {
            'id': 'W7_EDlXWTBiXAEEniNoMPwAAYuz9_1mcdex8MAXndPyIOAXndPyFyAO1OAA',
            'ext': 'mp4',
            'title': 'W7_EDlXWTBiXAEEniNoMPwAAYuz9_1mcdex8MAXndPyIOAXndPyFyAO1OAA',
            'thumbnail': 'https://s.sc-cdn.net/p9mgs8YyMZzfFRls4HGZxwXWBGVF-cEa6ZYPuCT2xPk=/default/preview.jpg',
            'description': '#spotlight',
            'timestamp': 1622914559,
            'upload_date': '20210605',
            'view_count': 62100,
            'uploader_id': None
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        schema_video_object_raw = self._html_search_regex(r'<script data-react-helmet="true" type="application/ld\+json">(.+)</script>',
                                                          webpage, 'schema_video_object')
        schema_video_object = self._parse_json(schema_video_object_raw, video_id, fatal=True)
        video_url = schema_video_object.get('contentUrl')
        title = schema_video_object.get('name')
        if not title:
            matching = re.match(r'sc-cdn.net/\w+/(\w+)', video_url)
            if matching:
                title = matching.group(1)
        if not title:
            title = video_id

        try:
            views = schema_video_object.get('interactionStatistic').get('userInteractionCount')
        except AttributeError:
            views = None

        try:
            uploader_id = schema_video_object.get('creator').get('alternateName')
        except AttributeError:
            uploader_id = None

        return {
            'id': video_id,
            'title': title,
            'url': video_url,
            'ext': 'mp4',
            'thumbnail': schema_video_object.get('thumbnailUrl'),
            'timestamp': unified_timestamp(schema_video_object.get('uploadDate')),
            'description': schema_video_object.get('description'),
            'duration': parse_duration(schema_video_object.get('duration')),
            'view_count': views,
            'uploader_id': uploader_id
        }
