from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    sanitized_Request,
)


class WistiaIE(InfoExtractor):
    _VALID_URL = r'https?://(?:fast\.)?wistia\.net/embed/iframe/(?P<id>[a-z0-9]+)'
    _API_URL = 'http://fast.wistia.com/embed/medias/{0:}.json'

    _TEST = {
        'url': 'http://fast.wistia.net/embed/iframe/sh7fpupwlt',
        'md5': 'cafeb56ec0c53c18c97405eecb3133df',
        'info_dict': {
            'id': 'sh7fpupwlt',
            'ext': 'mov',
            'title': 'Being Resourceful',
            'duration': 117,
        },
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)

        request = sanitized_Request(self._API_URL.format(video_id))
        request.add_header('Referer', url)  # Some videos require this.
        data_json = self._download_json(request, video_id)
        if data_json.get('error'):
            raise ExtractorError('Error while getting the playlist',
                                 expected=True)
        data = data_json['media']

        formats = []
        thumbnails = []
        for atype, a in data['assets'].items():
            if atype == 'still':
                thumbnails.append({
                    'url': a['url'],
                    'resolution': '%dx%d' % (a['width'], a['height']),
                })
                continue
            if atype == 'preview':
                continue
            formats.append({
                'format_id': atype,
                'url': a['url'],
                'width': a['width'],
                'height': a['height'],
                'filesize': a['size'],
                'ext': a['ext'],
                'preference': 1 if atype == 'original' else None,
            })

        self._sort_formats(formats)

        return {
            'id': video_id,
            'title': data['name'],
            'formats': formats,
            'thumbnails': thumbnails,
            'duration': data.get('duration'),
        }
