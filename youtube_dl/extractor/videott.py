from __future__ import unicode_literals

import re
import base64

from .common import InfoExtractor
from ..utils import (
    unified_strdate,
    int_or_none,
)


class VideoTtIE(InfoExtractor):
    ID_NAME = 'video.tt'
    IE_DESC = 'video.tt - Your True Tube'
    _VALID_URL = r'http://(?:www\.)?video\.tt/(?:(?:video|embed)/|watch_video\.php\?v=)(?P<id>[\da-zA-Z]{9})'

    _TESTS = [{
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
    }, {
        'url': 'http://video.tt/embed/amd5YujV8',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')

        settings = self._download_json(
            'http://www.video.tt/player_control/settings.php?v=%s' % video_id, video_id,
            'Downloading video JSON')['settings']

        video = settings['video_details']['video']

        formats = [
            {
                'url': base64.b64decode(res['u'].encode('utf-8')).decode('utf-8'),
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
            'view_count': int_or_none(video['view_count']),
            'comment_count': None if video.get('comment_count') == '--' else int_or_none(video['comment_count']),
            'like_count': int_or_none(video['liked']),
            'dislike_count': int_or_none(video['disliked']),
            'formats': formats,
        }
