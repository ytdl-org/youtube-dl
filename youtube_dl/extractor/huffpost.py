from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    parse_duration,
    unified_strdate,
)


class HuffPostIE(InfoExtractor):
    IE_DESC = 'Huffington Post'
    _VALID_URL = r'''(?x)
        https?://(embed\.)?live\.huffingtonpost\.com/
        (?:
            r/segment/[^/]+/|
            HPLEmbedPlayer/\?segmentId=
        )
        (?P<id>[0-9a-f]+)'''

    _TEST = {
        'url': 'http://live.huffingtonpost.com/r/segment/legalese-it/52dd3e4b02a7602131000677',
        'file': '52dd3e4b02a7602131000677.mp4',
        'md5': 'TODO',
        'info_dict': {
            'title': 'TODO',
            'description': 'TODO',
            'duration': 1549,
        }
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')

        api_url = 'http://embed.live.huffingtonpost.com/api/segments/%s.json' % video_id
        data = self._download_json(api_url, video_id)['data']

        video_title = data['title']
        duration = parse_duration(data['running_time'])
        upload_date = unified_strdate(data['schedule']['started_at'])

        thumbnails = []
        for url in data['images'].values():
            m = re.match('.*-([0-9]+x[0-9]+)\.', url)
            if not m:
                continue
            thumbnails.append({
                'url': url,
                'resolution': m.group(1),
            })

        formats = [{
            'format': key,
            'format_id': key.replace('/', '.'),
            'ext': 'mp4',
            'url': url,
            'vcodec': 'none' if key.startswith('audio/') else None,
        } for key, url in data['sources']['live'].items()]
        self._sort_formats(formats)

        return {
            'id': video_id,
            'title': video_title,
            'formats': formats,
            'duration': duration,
            'upload_date': upload_date,
            'thumbnails': thumbnails,
        }
