# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor


class ArnesIE(InfoExtractor):
    IE_NAME = 'video.arnes.si'
    IE_DESC = 'Arnes Video'
    _VALID_URL = r'https?://(?:www\.)?video.arnes\.si/(watch|embed)/(?P<id>[a-zA-Z1-9]{12})'
    _TESTS = [{
        'url': 'https://video.arnes.si/watch/a1qrWTOQfVoU',
        'md5': '75ab8384b71106b64dd8a23b105ef650',
        'info_dict': {
            'id': 'a1qrWTOQfVoU',
            'ext': 'mp4',
            'title': 'Linearna neodvisnost, definicija',
            'creator': 'Polona Oblak',
            'description': 'Linearna neodvisnost, definicija'
        }
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)

        video_info = self._download_json(f'https://video.arnes.si/api/public/video/{video_id}', video_id).get('data')

        formats = []
        for format in video_info.get('media'):
            formats.append({
                'url': 'https://video.arnes.si' + format.get('url'),
                'ext': 'mp4',
                'width': format.get('width'),
                'height': format.get('height')
            })

        return {
            'id': video_id,
            'title': video_info.get('title'),
            'description': video_info.get('description'),
            'duration': video_info.get('duration') / 100,
            'view_count': video_info.get('views'),
            'creator': video_info.get('author'),
            'formats': formats
        }
