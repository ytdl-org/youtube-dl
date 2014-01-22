from __future__ import unicode_literals

import datetime
import json
import re

from .common import InfoExtractor
from ..utils import (
    remove_start,
)


class BlinkxIE(InfoExtractor):
    _VALID_URL = r'^(?:https?://(?:www\.)blinkx\.com/#?ce/|blinkx:)(?P<id>[^?]+)'
    IE_NAME = 'blinkx'

    _TEST = {
        'url': 'http://www.blinkx.com/ce/8aQUy7GVFYgFzpKhT0oqsilwOGFRVXk3R1ZGWWdGenBLaFQwb3FzaWx3OGFRVXk3R1ZGWWdGenB',
        'file': '8aQUy7GV.mp4',
        'md5': '2e9a07364af40163a908edbf10bb2492',
        'info_dict': {
            "title": "Police Car Rolls Away",
            "uploader": "stupidvideos.com",
            "upload_date": "20131215",
            "description": "A police car gently rolls away from a fight. Maybe it felt weird being around a confrontation and just had to get out of there!",
            "duration": 14.886,
            "thumbnails": [{
                "width": 100,
                "height": 76,
                "url": "http://cdn.blinkx.com/stream/b/41/StupidVideos/20131215/1873969261/1873969261_tn_0.jpg",
            }],
        },
    }

    def _real_extract(self, rl):
        m = re.match(self._VALID_URL, rl)
        video_id = m.group('id')
        display_id = video_id[:8]

        api_url = (u'https://apib4.blinkx.com/api.php?action=play_video&' +
                   'video=%s' % video_id)
        data_json = self._download_webpage(api_url, display_id)
        data = json.loads(data_json)['api']['results'][0]
        dt = datetime.datetime.fromtimestamp(data['pubdate_epoch'])
        pload_date = dt.strftime('%Y%m%d')

        duration = None
        thumbnails = []
        formats = []
        for m in data['media']:
            if m['type'] == 'jpg':
                thumbnails.append({
                    'url': m['link'],
                    'width': int(m['w']),
                    'height': int(m['h']),
                })
            elif m['type'] == 'original':
                duration = m['d']
            elif m['type'] == 'youtube':
                yt_id = m['link']
                self.to_screen(u'Youtube video detected: %s' % yt_id)
                return self.url_result(yt_id, 'Youtube', video_id=yt_id)
            elif m['type'] in ('flv', 'mp4'):
                vcodec = remove_start(m['vcodec'], 'ff')
                acodec = remove_start(m['acodec'], 'ff')
                tbr = (int(m['vbr']) + int(m['abr'])) // 1000
                format_id = (u'%s-%sk-%s' %
                             (vcodec,
                              tbr,
                              m['w']))
                formats.append({
                    'format_id': format_id,
                    'url': m['link'],
                    'vcodec': vcodec,
                    'acodec': acodec,
                    'abr': int(m['abr']) // 1000,
                    'vbr': int(m['vbr']) // 1000,
                    'tbr': tbr,
                    'width': int(m['w']),
                    'height': int(m['h']),
                })

        self._sort_formats(formats)

        return {
            'id': display_id,
            'fullid': video_id,
            'title': data['title'],
            'formats': formats,
            'uploader': data['channel_name'],
            'upload_date': pload_date,
            'description': data.get('description'),
            'thumbnails': thumbnails,
            'duration': duration,
        }
