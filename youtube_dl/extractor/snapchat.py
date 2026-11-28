# coding: utf-8
from __future__ import unicode_literals

from ..utils import unified_timestamp, parse_duration, try_get, str_or_none, ExtractorError
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
            'thumbnail': r're:https://s\.sc-cdn\.net/.+\.jpg',
            'description': '#spotlight',
            'timestamp': 1622914559,
            'upload_date': '20210605',
            'view_count': 72100,
            'uploader_id': None
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        schema_video_object_raw = self._html_search_regex(r'<script\s[^>]*?data-react-helmet\s*=\s*"true"\s[^>]*?type\s*=\s*"application/ld\+json">(.+?)</script>',
                                                          webpage, 'schema_video_object')
        schema_video_object = self._parse_json(schema_video_object_raw, video_id, fatal=True)
        try:
            video_url = str_or_none(schema_video_object['contentUrl'])
            if not video_url:
                raise ValueError('video_url must be non-empty string')
        except (TypeError, ValueError) as e:
            raise ExtractorError('Unexpected format for schema_video_object', cause=e, video_id=video_id)

        title = schema_video_object.get('name')
        if not title:
            title = self._generic_title(url)

        views = try_get(schema_video_object.get('interactionStatistic'), lambda x: x['userInteractionCount'])

        uploader_id = try_get(schema_video_object.get('creator'), lambda x: x['alternateName'])

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
