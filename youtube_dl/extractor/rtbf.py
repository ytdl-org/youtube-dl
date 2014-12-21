# coding: utf-8
from __future__ import unicode_literals

import re
import json

from .common import InfoExtractor


class RTBFIE(InfoExtractor):
    _VALID_URL = r'https?://www.rtbf.be/video/[^\?]+\?id=(?P<id>\d+)'
    _TEST = {
        'url': 'https://www.rtbf.be/video/detail_les-diables-au-coeur-episode-2?id=1921274',
        'md5': '799f334ddf2c0a582ba80c44655be570',
        'info_dict': {
            'id': '1921274',
            'ext': 'mp4',
            'title': 'Les Diables au coeur (épisode 2)',
            'description': 'Football - Diables Rouges',
            'duration': 3099,
            'timestamp': 1398456336,
            'upload_date': '20140425',
        }
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')

        page = self._download_webpage('https://www.rtbf.be/video/embed?id=%s' % video_id, video_id)

        data = json.loads(self._html_search_regex(
            r'<div class="js-player-embed(?: player-embed)?" data-video="([^"]+)"', page, 'data video'))['data']

        video_url = data.get('downloadUrl') or data.get('url')

        if data['provider'].lower() == 'youtube':
            return self.url_result(video_url, 'Youtube')

        return {
            'id': video_id,
            'url': video_url,
            'title': data['title'],
            'description': data.get('description') or data.get('subtitle'),
            'thumbnail': data['thumbnail']['large'],
            'duration': data.get('duration') or data.get('realDuration'),
            'timestamp': data['created'],
            'view_count': data['viewCount'],
        }
