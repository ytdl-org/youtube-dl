from __future__ import unicode_literals

import json
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
                'thumbnail': 're:^http://frame\.thestaticvube\.com/snap/[0-9x]+/102e7e63057-5ebc-4f5c-4065-6ce4ebde131f\.jpg$',
                'uploader': 'Chiara.Grispo',
                'timestamp': 1388743358,
                'upload_date': '20140103',
                'duration': 170.56,
                'like_count': int,
                'dislike_count': int,
                'comment_count': int,
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
                'thumbnail': 're:^http://frame\.thestaticvube\.com/snap/[0-9x]+/102265d5a9f-0f17-4f6b-5753-adf08484ee1e\.jpg$',
                'uploader': 'Seraina',
                'timestamp': 1396492438,
                'upload_date': '20140403',
                'duration': 240.107,
                'like_count': int,
                'dislike_count': int,
                'comment_count': int,
            }
        }, {
            'url': 'http://vube.com/vote/Siren+Gene/0nmsMY5vEq?n=2&t=s',
            'md5': '0584fc13b50f887127d9d1007589d27f',
            'info_dict': {
                'id': '0nmsMY5vEq',
                'ext': 'mp4',
                'title': 'Frozen - Let It Go Cover by Siren Gene',
                'description': 'My rendition of "Let It Go" originally sung by Idina Menzel.',
                'uploader': 'Siren Gene',
                'uploader_id': 'Siren',
                'thumbnail': 're:^http://frame\.thestaticvube\.com/snap/[0-9x]+/10283ab622a-86c9-4681-51f2-30d1f65774af\.jpg$',
                'duration': 221.788,
                'like_count': int,
                'dislike_count': int,
                'comment_count': int,
            }
        }
    ]

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')

        webpage = self._download_webpage(url, video_id)
        data_json = self._search_regex(
            r'(?s)window\["(?:tapiVideoData|vubeOriginalVideoData)"\]\s*=\s*(\{.*?\n});\n',
            webpage, 'video data'
        )
        data = json.loads(data_json)
        video = (
            data.get('video') or
            data)
        assert isinstance(video, dict)

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
        thumbnail = self._proto_relative_url(
            video.get('thumbnail') or video.get('thumbnail_src'),
            scheme='http:')
        uploader = data.get('user', {}).get('channel', {}).get('name') or video.get('user_alias')
        uploader_id = data.get('user', {}).get('name')
        timestamp = int_or_none(video.get('upload_time'))
        duration = video['duration']
        view_count = video.get('raw_view_count')
        like_count = video.get('rlikes')
        if like_count is None:
            like_count = video.get('total_likes')
        dislike_count = video.get('rhates')
        if dislike_count is None:
            dislike_count = video.get('total_hates')

        comments = video.get('comments')
        comment_count = None
        if comments is None:
            comment_data = self._download_json(
                'http://vube.com/api/video/%s/comment' % video_id,
                video_id, 'Downloading video comment JSON', fatal=False)
            if comment_data is not None:
                comment_count = int_or_none(comment_data.get('total'))
        else:
            comment_count = len(comments)

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
