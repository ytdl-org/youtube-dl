from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import int_or_none


class VubeIE(InfoExtractor):
    IE_NAME = 'vube'
    IE_DESC = 'Vube.com'
    _VALID_URL = r'http://vube\.com/(?:[^/]+/)+(?P<id>[\da-zA-Z]{10})\b'

    _TESTS = [
        {
            'url': 'http://vube.com/Chiara+Grispo+Video+Channel/YL2qNPkqon',
            'md5': 'db7aba89d4603dadd627e9d1973946fe',
            'info_dict': {
                'id': 'YL2qNPkqon',
                'ext': 'mp4',
                'title': 'Chiara Grispo - Price Tag by Jessie J',
                'description': 'md5:8ea652a1f36818352428cb5134933313',
                'thumbnail': 'http://frame.thestaticvube.com/snap/228x128/102e7e63057-5ebc-4f5c-4065-6ce4ebde131f.jpg',
                'uploader': 'Chiara.Grispo',
                'uploader_id': '1u3hX0znhP',
                'timestamp': 1388743358,
                'upload_date': '20140103',
                'duration': 170.56
            }
        },
        {
            'url': 'http://vube.com/SerainaMusic/my-7-year-old-sister-and-i-singing-alive-by-krewella/UeBhTudbfS?t=s&n=1',
            'md5': '5d4a52492d76f72712117ce6b0d98d08',
            'info_dict': {
                'id': 'UeBhTudbfS',
                'ext': 'mp4',
                'title': 'My 7 year old Sister and I singing "Alive" by Krewella',
                'description': 'md5:40bcacb97796339f1690642c21d56f4a',
                'thumbnail': 'http://frame.thestaticvube.com/snap/228x128/102265d5a9f-0f17-4f6b-5753-adf08484ee1e.jpg',
                'uploader': 'Seraina',
                'uploader_id': 'XU9VE2BQ2q',
                'timestamp': 1396492438,
                'upload_date': '20140403',
                'duration': 240.107
            }
        }
    ]

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')

        video = self._download_json(
            'http://vube.com/api/v2/video/%s' % video_id, video_id, 'Downloading video JSON')

        public_id = video['public_id']

        formats = [
            {
                'url': 'http://video.thestaticvube.com/video/%s/%s.mp4' % (fmt['media_resolution_id'], public_id),
                'height': int(fmt['height']),
                'abr': int(fmt['audio_bitrate']),
                'vbr': int(fmt['video_bitrate']),
                'format_id': fmt['media_resolution_id']
            } for fmt in video['mtm'] if fmt['transcoding_status'] == 'processed'
        ]

        self._sort_formats(formats)

        title = video['title']
        description = video.get('description')
        thumbnail = video['thumbnail_src']
        if thumbnail.startswith('//'):
            thumbnail = 'http:' + thumbnail
        uploader = video['user_alias']
        uploader_id = video['user_url_id']
        timestamp = int(video['upload_time'])
        duration = video['duration']
        view_count = video.get('raw_view_count')
        like_count = video.get('total_likes')
        dislike_count= video.get('total_hates')

        comment = self._download_json(
            'http://vube.com/api/video/%s/comment' % video_id, video_id, 'Downloading video comment JSON')

        comment_count = int_or_none(comment.get('total'))

        return {
            'id': video_id,
            'formats': formats,
            'title': title,
            'description': description,
            'thumbnail': thumbnail,
            'uploader': uploader,
            'uploader_id': uploader_id,
            'timestamp': timestamp,
            'duration': duration,
            'view_count': view_count,
            'like_count': like_count,
            'dislike_count': dislike_count,
            'comment_count': comment_count,
        }
