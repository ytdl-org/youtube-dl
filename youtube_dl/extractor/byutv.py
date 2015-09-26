from __future__ import unicode_literals

import json
import re

from .common import InfoExtractor
from ..utils import ExtractorError


class BYUtvIE(InfoExtractor):
    _VALID_URL = r'^https?://(?:www\.)?byutv.org/watch/[0-9a-f-]+/(?P<video_id>[^/?#]+)'
    _TEST = {
        'url': 'http://www.byutv.org/watch/6587b9a3-89d2-42a6-a7f7-fd2f81840a7d/studio-c-season-5-episode-5',
        'info_dict': {
            'id': 'studio-c-season-5-episode-5',
            'ext': 'mp4',
            'description': 'md5:5438d33774b6bdc662f9485a340401cc',
            'title': 'Season 5 Episode 5',
            'thumbnail': 're:^https?://.*\.jpg$'
        },
        'params': {
            'skip_download': True,
        }
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('video_id')

        webpage = self._download_webpage(url, video_id)
        episode_code = self._search_regex(
            r'(?s)episode:(.*?\}),\s*\n', webpage, 'episode information')
        episode_json = re.sub(
            r'(\n\s+)([a-zA-Z]+):\s+\'(.*?)\'', r'\1"\2": "\3"', episode_code)
        ep = json.loads(episode_json)

        if ep['providerType'] == 'Ooyala':
            return {
                '_type': 'url_transparent',
                'ie_key': 'Ooyala',
                'url': 'ooyala:%s' % ep['providerId'],
                'id': video_id,
                'title': ep['title'],
                'description': ep.get('description'),
                'thumbnail': ep.get('imageThumbnail'),
            }
        else:
            raise ExtractorError('Unsupported provider %s' % ep['provider'])
