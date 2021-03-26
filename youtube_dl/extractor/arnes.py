# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor


class ArnesIE(InfoExtractor):
    IE_NAME = 'video.arnes.si'
    IE_DESC = 'Arnes Video'
    _VALID_URL = r'https?:\/\/video.arnes\.si\/(en\/)?(watch|embed|api\/asset)\/(?P<id>[a-zA-Z1-9]{12}).*'
    _TESTS = [{
        'url': 'https://video.arnes.si/watch/a1qrWTOQfVoU',  # Normal url
        'md5': '75ab8384b71106b64dd8a23b105ef650',
        'info_dict': {
            'id': 'a1qrWTOQfVoU',
            'ext': 'mp4',
            'title': 'Linearna neodvisnost, definicija',
            'creator': 'Polona Oblak',
            'description': 'Linearna neodvisnost, definicija'
        }
    }, {
        'url': 'https://video.arnes.si/api/asset/s1YjnV7hadlC/play.mp4',  # API url
        'md5': 'e29ccea409ec7c958f5cb82774cadd77',
        'info_dict': {
            'id': 's1YjnV7hadlC',
            'ext': 'mp4',
            'title': 'Install Gentoo',
            'creator': 'Filip Kristan',
            'description': 'Install Gentoo'
        }
    }, {
        'url': 'https://video.arnes.si/embed/s1YjnV7hadlC',  # Embed url
        'only_matching': True,
    }, {
        'url': 'https://video.arnes.si/en/watch/s1YjnV7hadlC',  # English url
        'only_matching': True,
    }, {
        'url': 'https://video.arnes.si/embed/s1YjnV7hadlC?t=123&hideRelated=1',  # Url with GET parameters
        'only_matching': True,
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)

        # Video information is available at https://video.arnes.si/api/public/video/{video_id}
        video_info = self._download_json('https://video.arnes.si/api/public/video/' + video_id, video_id).get('data')

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
