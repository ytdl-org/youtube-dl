from __future__ import unicode_literals

import re
import json

from .common import InfoExtractor
from ..utils import compat_urllib_request


class VeohIE(InfoExtractor):
    _VALID_URL = r'http://(?:www\.)?veoh\.com/(?:watch|iphone/#_Watch)/v(?P<id>\d*)'

    _TEST = {
        'url': 'http://www.veoh.com/watch/v56314296nk7Zdmz3',
        'file': '56314296.mp4',
        'md5': '620e68e6a3cff80086df3348426c9ca3',
        'info_dict': {
            'title': 'Straight Backs Are Stronger',
            'uploader': 'LUMOback',
            'description': 'At LUMOback, we believe straight backs are stronger.  The LUMOback Posture & Movement Sensor:  It gently vibrates when you slouch, inspiring improved posture and mobility.  Use the app to track your data and improve your posture over time. ',
        }
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')
        webpage = self._download_webpage(url, video_id)
        age_limit = 0
        if 'class="adultwarning-container"' in webpage:
            self.report_age_confirmation()
            age_limit = 18
            request = compat_urllib_request.Request(url)
            request.add_header('Cookie', 'confirmedAdult=true')
            webpage = self._download_webpage(request, video_id)

        m_youtube = re.search(r'http://www\.youtube\.com/v/(.*?)(\&|")', webpage)
        if m_youtube is not None:
            youtube_id = m_youtube.group(1)
            self.to_screen('%s: detected Youtube video.' % video_id)
            return self.url_result(youtube_id, 'Youtube')

        self.report_extraction(video_id)
        info = self._search_regex(r'videoDetailsJSON = \'({.*?})\';', webpage, 'info')
        info = json.loads(info)
        video_url = info.get('fullPreviewHashHighPath') or info.get('fullPreviewHashLowPath')

        return {
            'id': info['videoId'],
            'title': info['title'],
            'url': video_url,
            'uploader': info['username'],
            'thumbnail': info.get('highResImage') or info.get('medResImage'),
            'description': info['description'],
            'view_count': info['views'],
            'age_limit': age_limit,
        }
