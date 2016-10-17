from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    sanitized_Request,
    int_or_none,
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
            'description': 'a Clients From Hell Video Series video from worldwidewebhosting',
            'upload_date': '20131204',
            'timestamp': 1386185018,
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
        title = data['name']

        formats = []
        thumbnails = []
        for a in data['assets']:
            astatus = a.get('status')
            atype = a.get('type')
            if (astatus is not None and astatus != 2) or atype == 'preview':
                continue
            elif atype in ('still', 'still_image'):
                thumbnails.append({
                    'url': a['url'],
                    'resolution': '%dx%d' % (a['width'], a['height']),
                })
            else:
                formats.append({
                    'format_id': atype,
                    'url': a['url'],
                    'tbr': int_or_none(a.get('bitrate')),
                    'vbr': int_or_none(a.get('opt_vbitrate')),
                    'width': int_or_none(a.get('width')),
                    'height': int_or_none(a.get('height')),
                    'filesize': int_or_none(a.get('size')),
                    'vcodec': a.get('codec'),
                    'container': a.get('container'),
                    'ext': a.get('ext'),
                    'preference': 1 if atype == 'original' else None,
                })

        self._sort_formats(formats)

        return {
            'id': video_id,
            'title': title,
            'description': data.get('seoDescription'),
            'formats': formats,
            'thumbnails': thumbnails,
            'duration': int_or_none(data.get('duration')),
            'timestamp': int_or_none(data.get('createdAt')),
        }
