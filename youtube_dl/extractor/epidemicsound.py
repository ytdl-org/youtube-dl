# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from datetime import datetime


class EpidemicSoundIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?epidemicsound\.com/track/(?P<id>[0-9a-zA-Z]+)'
    _TEST = {
        'url': 'https://www.epidemicsound.com/track/yFfQVRpSPz/',
        'md5': 'd98ff2ddb49e8acab9716541cbc9dfac',
        'info_dict': {
            'id': 'yFfQVRpSPz',
            'ext': 'mp3',
            'tags': ['foley', 'door', 'knock', 'glass', 'window', 'glass door knock'],
            'title': 'Door Knock Door 1',
            'duration': 1,
            'thumbnail': 'https://cdn.epidemicsound.com/curation-assets/commercial-release-cover-images/default-sfx/3000x3000.jpg',
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        json_data = self._download_json('https://www.epidemicsound.com/json/track/' + video_id, video_id)
        title = json_data.get('title')
        image_url = json_data.get('imageUrl')
        media_url = json_data.get('stems').get('full').get('lqMp3Url')
        media_len = json_data.get('length')
        timestamp = int(datetime.strptime(json_data.get('added'), '%Y-%m-%dT%H:%M:%S').timestamp())
        tags = json_data.get('metadataTags')

        return {
            'id': video_id,
            'url': media_url,
            'tags': tags,
            'title': title,
            'duration': media_len,
            'timestamp': timestamp,
            'thumbnail': image_url,
        }