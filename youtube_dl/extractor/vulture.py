from __future__ import unicode_literals

import json
import os.path
import re

from .common import InfoExtractor
from ..utils import (
    int_or_none,
    parse_iso8601,
)


class VultureIE(InfoExtractor):
    IE_NAME = 'vulture.com'
    _VALID_URL = r'https?://video\.vulture\.com/video/(?P<display_id>[^/]+)/'
    _TEST = {
        'url': 'http://video.vulture.com/video/Mindy-Kaling-s-Harvard-Speech/player?layout=compact&read_more=1',
        'md5': '8d997845642a2b5152820f7257871bc8',
        'info_dict': {
            'id': '6GHRQL3RV7MSD1H4',
            'ext': 'mp4',
            'title': 'kaling-speech-2-MAGNIFY STANDARD CONTAINER REVISED',
            'uploader_id': 'Sarah',
            'thumbnail': 're:^http://.*\.jpg$',
            'timestamp': 1401288564,
            'upload_date': '20140528',
            'description': 'Uplifting and witty, as predicted.',
            'duration': 1015,
        }
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        display_id = mobj.group('display_id')

        webpage = self._download_webpage(url, display_id)
        query_string = self._search_regex(
            r"queryString\s*=\s*'([^']+)'", webpage, 'query string')
        video_id = self._search_regex(
            r'content=([^&]+)', query_string, 'video ID')
        query_url = 'http://video.vulture.com/embed/player/container/1000/1000/?%s' % query_string

        query_webpage = self._download_webpage(
            query_url, display_id, note='Downloading query page')
        params_json = self._search_regex(
            r'(?sm)new MagnifyEmbeddablePlayer\({.*?contentItem:\s*(\{.*?\})\n,\n',
            query_webpage,
            'player params')
        params = json.loads(params_json)

        upload_timestamp = parse_iso8601(params['posted'].replace(' ', 'T'))
        uploader_id = params.get('user', {}).get('handle')

        media_item = params['media_item']
        title = os.path.splitext(media_item['title'])[0]
        duration = int_or_none(media_item.get('duration_seconds'))

        return {
            'id': video_id,
            'display_id': display_id,
            'url': media_item['pipeline_xid'],
            'title': title,
            'timestamp': upload_timestamp,
            'thumbnail': params.get('thumbnail_url'),
            'uploader_id': uploader_id,
            'description': params.get('description'),
            'duration': duration,
        }
