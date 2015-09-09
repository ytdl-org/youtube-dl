from __future__ import unicode_literals

from .common import InfoExtractor, ExtractorError
from ..utils import (
    int_or_none,
    float_or_none,
    parse_iso8601,
)


class VidmeIE(InfoExtractor):
    _VALID_URL = r'https?://vid\.me/(?:e/)?(?P<id>[\da-zA-Z]+)'
    _TESTS = [{
        'url': 'https://vid.me/QNB',
        'md5': 'c62f1156138dc3323902188c5b5a8bd6',
        'info_dict': {
            'id': 'QNB',
            'ext': 'mp4',
            'title': 'Fishing for piranha - the easy way',
            'description': 'source: https://www.facebook.com/photo.php?v=312276045600871',
            'duration': 119.92,
            'timestamp': 1406313244,
            'upload_date': '20140725',
            'thumbnail': 're:^https?://.*\.jpg',
            'view_count': int,
            'like_count': int,
            'comment_count': int,
        },
    }, {
        'url': 'https://vid.me/Gc6M',
        'md5': 'f42d05e7149aeaec5c037b17e5d3dc82',
        'info_dict': {
            'id': 'Gc6M',
            'ext': 'mp4',
            'title': 'O Mere Dil ke chain - Arnav and Khushi VM',
            'duration': 223.72,
            'timestamp': 1441211642,
            'upload_date': '20150902',
            'thumbnail': 're:^https?://.*\.jpg',
            'view_count': int,
            'like_count': int,
            'comment_count': int,
            'comment_count': int,
        },
        'params': {
            'skip_download': True,
        },
    }, {
        # tests uploader field
        'url': 'https://vid.me/4Iib',
        'info_dict': {
            'id': '4Iib',
            'ext': 'mp4',
            'title': 'The Carver',
            'description': 'md5:e9c24870018ae8113be936645b93ba3c',
            'duration': 97.859999999999999,
            'timestamp': 1433203629,
            'upload_date': '20150602',
            'uploader': 'Thomas',
            'thumbnail': 're:^https?://.*\.jpg',
            'view_count': int,
            'like_count': int,
            'comment_count': int,
        },
        'params': {
            'skip_download': True,
        },
    }, {
        # From http://naked-yogi.tumblr.com/post/118312946248/naked-smoking-stretching
        'url': 'https://vid.me/e/Wmur',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        api_url = 'https://api.vid.me/videoByUrl/' + video_id
        data = self._download_json(api_url, video_id)

        video_data = data.get('video')
        if video_data is None:
            raise ExtractorError('Could not extract the vid.me video data')

        title = video_data.get('title')
        description = video_data.get('description')
        thumbnail = video_data.get('thumbnail_url')
        timestamp = parse_iso8601(video_data.get('date_created'), ' ')
        duration = float_or_none(video_data.get('duration'))
        view_count = int_or_none(video_data.get('view_count'))
        like_count = int_or_none(video_data.get('likes_count'))
        comment_count = int_or_none(video_data.get('comment_count'))

        uploader = None
        user_data = video_data.get('user')
        if user_data is not None:
            uploader = user_data.get('username')

        formats = [{
            'format_id': format['type'],
            'url': format['uri'],
            'width': int_or_none(format['width']),
            'height': int_or_none(format['height']),
        } for format in video_data.get('formats', [])]
        self._sort_formats(formats)

        return {
            'id': video_id,
            'title': title,
            'description': description,
            'thumbnail': thumbnail,
            'timestamp': timestamp,
            'duration': duration,
            'view_count': view_count,
            'like_count': like_count,
            'comment_count': comment_count,
            'uploader': uploader,
            'formats': formats,
        }
