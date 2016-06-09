# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import (
    qualities,
    parse_iso8601
)


class RockstarGamesIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?rockstargames\.com/videos/video/(?P<id>[0-9]+)'
    _TEST = {
        'url': 'https://www.rockstargames.com/videos/video/11544/',
        'md5': '03b5caa6e357a4bd50e3143fc03e5733',
        'info_dict': {
            'id': '11544',
            'ext': 'mp4',
            'title': 'Further Adventures in Finance and Felony Trailer',
            'thumbnail': 're:^https?://.*\.jpg$',
            'description': 'md5:6d31f55f30cb101b5476c4a379e324a3',
            'upload_date': '20160602',
            'timestamp': 1464876000
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        json_data = self._download_json(
            'https://www.rockstargames.com/videoplayer/videos/get-video.json?id=%s&locale=en_us' % video_id,
            video_id
        )['video']

        formats = []

        for video in json_data['files_processed']['video/mp4']:
            if not video.get('src'):
                continue
            height = video.get('resolution', '').replace('p', '')
            
            formats.append({
                'url': self._proto_relative_url(video['src']),
                'height': int(height) if height.isdigit() else -1,
            })
        self._sort_formats(formats)

        return {
            'id': video_id,
            'title': json_data['title'],
            'description': json_data.get('description'),
            'formats': formats,
            'thumbnail': self._proto_relative_url(json_data.get('screencap')),
            'timestamp': parse_iso8601(json_data.get('created'))
        }
