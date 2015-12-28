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
        'md5': '55f5e8981c1c80a64706a44b74833de8',
        'info_dict': {
            'id': '52dd3e4b02a7602131000677',
            'ext': 'mp4',
            'title': 'Legalese It! with @MikeSacksHP',
            'description': 'This week on Legalese It, Mike talks to David Bosco about his new book on the ICC, "Rough Justice," he also discusses the Virginia AG\'s historic stance on gay marriage, the execution of Edgar Tamayo, the ICC\'s delay of Kenya\'s President and more.  ',
            'duration': 1549,
            'upload_date': '20140124',
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)

        api_url = 'http://embed.live.huffingtonpost.com/api/segments/%s.json' % video_id
        data = self._download_json(api_url, video_id)['data']

        video_title = data['title']
        duration = parse_duration(data.get('running_time'))
        upload_date = unified_strdate(
            data.get('schedule', {}).get('starts_at') or data.get('segment_start_date_time'))
        description = data.get('description')

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
        } for key, url in data.get('sources', {}).get('live', {}).items()]

        if not formats and data.get('fivemin_id'):
            return self.url_result('5min:%s' % data['fivemin_id'])

        self._sort_formats(formats)

        return {
            'id': video_id,
            'title': video_title,
            'description': description,
            'formats': formats,
            'duration': duration,
            'upload_date': upload_date,
            'thumbnails': thumbnails,
        }
