from __future__ import unicode_literals

import re
import base64

from .common import InfoExtractor
from ..utils import unified_strdate


class VideoTtIE(InfoExtractor):
    ID_NAME = 'video.tt'
    IE_DESC = 'video.tt - Your True Tube'
    _VALID_URL = r'http://(?:www\.)?video\.tt/(?:video/|watch_video\.php\?v=)(?P<id>[\da-zA-Z]{9})'

    _TEST = {
        'url': 'http://www.video.tt/watch_video.php?v=amd5YujV8',
        'md5': 'b13aa9e2f267effb5d1094443dff65ba',
        'info_dict': {
            'id': 'amd5YujV8',
            'ext': 'flv',
            'title': 'Motivational video Change your mind in just 2.50 mins',
            'description': '',
            'upload_date': '20130827',
            'uploader': 'joseph313',
        }
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')

        settings = self._download_json(
            'http://www.video.tt/player_control/settings.php?v=%s' % video_id, video_id,
            'Downloading video JSON')['settings']

        video = settings['video_details']['video']

        formats = [
            {
                'url': base64.b64decode(res['u']).decode('utf-8'),
                'ext': 'flv',
                'format_id': res['l'],
            } for res in settings['res'] if res['u']
        ]

        return {
            'id': video_id,
            'title': video['title'],
            'description': video['description'],
            'thumbnail': settings['config']['thumbnail'],
            'upload_date': unified_strdate(video['added']),
            'uploader': video['owner'],
            'view_count': int(video['view_count']),
            'comment_count': int(video['comment_count']),
            'like_count': int(video['liked']),
            'dislike_count': int(video['disliked']),
            'formats': formats,
        }