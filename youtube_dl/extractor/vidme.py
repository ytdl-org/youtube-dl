from __future__ import unicode_literals

from .common import InfoExtractor
from ..compat import compat_HTTPError
from ..utils import (
    ExtractorError,
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
            'thumbnail': 're:^https?://.*\.jpg',
            'timestamp': 1406313244,
            'upload_date': '20140725',
            'age_limit': 0,
            'duration': 119.92,
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
            'thumbnail': 're:^https?://.*\.jpg',
            'timestamp': 1441211642,
            'upload_date': '20150902',
            'uploader': 'SunshineM',
            'uploader_id': '3552827',
            'age_limit': 0,
            'duration': 223.72,
            'view_count': int,
            'like_count': int,
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
            'thumbnail': 're:^https?://.*\.jpg',
            'timestamp': 1433203629,
            'upload_date': '20150602',
            'uploader': 'Thomas',
            'uploader_id': '109747',
            'age_limit': 0,
            'duration': 97.859999999999999,
            'view_count': int,
            'like_count': int,
            'comment_count': int,
        },
        'params': {
            'skip_download': True,
        },
    }, {
        # nsfw test from http://naked-yogi.tumblr.com/post/118312946248/naked-smoking-stretching
        'url': 'https://vid.me/e/Wmur',
        'info_dict': {
            'id': 'Wmur',
            'ext': 'mp4',
            'title': 'naked smoking & stretching',
            'thumbnail': 're:^https?://.*\.jpg',
            'timestamp': 1430931613,
            'upload_date': '20150506',
            'uploader': 'naked-yogi',
            'uploader_id': '1638622',
            'age_limit': 18,
            'duration': 653.26999999999998,
            'view_count': int,
            'like_count': int,
            'comment_count': int,
        },
        'params': {
            'skip_download': True,
        },
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)

        try:
            response = self._download_json(
                'https://api.vid.me/videoByUrl/%s' % video_id, video_id)
        except ExtractorError as e:
            if isinstance(e.cause, compat_HTTPError) and e.cause.code == 400:
                response = self._parse_json(e.cause.read(), video_id)
            else:
                raise

        error = response.get('error')
        if error:
            raise ExtractorError(
                '%s returned error: %s' % (self.IE_NAME, error), expected=True)

        video = response['video']

        formats = [{
            'format_id': f.get('type'),
            'url': f['uri'],
            'width': int_or_none(f.get('width')),
            'height': int_or_none(f.get('height')),
            'preference': 0 if f.get('type', '').endswith('clip') else 1,
        } for f in video.get('formats', []) if f.get('uri')]
        self._sort_formats(formats)

        title = video['title']
        description = video.get('description')
        thumbnail = video.get('thumbnail_url')
        timestamp = parse_iso8601(video.get('date_created'), ' ')
        uploader = video.get('user', {}).get('username')
        uploader_id = video.get('user', {}).get('user_id')
        age_limit = 18 if video.get('nsfw') is True else 0
        duration = float_or_none(video.get('duration'))
        view_count = int_or_none(video.get('view_count'))
        like_count = int_or_none(video.get('likes_count'))
        comment_count = int_or_none(video.get('comment_count'))

        return {
            'id': video_id,
            'title': title,
            'description': description,
            'thumbnail': thumbnail,
            'uploader': uploader,
            'uploader_id': uploader_id,
            'age_limit': age_limit,
            'timestamp': timestamp,
            'duration': duration,
            'view_count': view_count,
            'like_count': like_count,
            'comment_count': comment_count,
            'formats': formats,
        }
