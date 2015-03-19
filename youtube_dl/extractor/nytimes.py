from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import (
    float_or_none,
    int_or_none,
    parse_iso8601,
)


class NYTimesIE(InfoExtractor):
    _VALID_URL = r'https?://(?:(?:www\.)?nytimes\.com/video/(?:[^/]+/)+?|graphics8\.nytimes\.com/bcvideo/\d+(?:\.\d+)?/iframe/embed\.html\?videoId=)(?P<id>\d+)'

    _TESTS = [{
        'url': 'http://www.nytimes.com/video/opinion/100000002847155/verbatim-what-is-a-photocopier.html?playlistId=100000001150263',
        'md5': '18a525a510f942ada2720db5f31644c0',
        'info_dict': {
            'id': '100000002847155',
            'ext': 'mov',
            'title': 'Verbatim: What Is a Photocopier?',
            'description': 'md5:93603dada88ddbda9395632fdc5da260',
            'timestamp': 1398631707,
            'upload_date': '20140427',
            'uploader': 'Brett Weiner',
            'duration': 419,
        }
    }, {
        'url': 'http://www.nytimes.com/video/travel/100000003550828/36-hours-in-dubai.html',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)

        video_data = self._download_json(
            'http://www.nytimes.com/svc/video/api/v2/video/%s' % video_id,
            video_id, 'Downloading video JSON')

        title = video_data['headline']
        description = video_data.get('summary')
        duration = float_or_none(video_data.get('duration'), 1000)

        uploader = video_data['byline']
        timestamp = parse_iso8601(video_data['publication_date'][:-8])

        def get_file_size(file_size):
            if isinstance(file_size, int):
                return file_size
            elif isinstance(file_size, dict):
                return int(file_size.get('value', 0))
            else:
                return 0

        formats = [
            {
                'url': video['url'],
                'format_id': video.get('type'),
                'vcodec': video.get('video_codec'),
                'width': int_or_none(video.get('width')),
                'height': int_or_none(video.get('height')),
                'filesize': get_file_size(video.get('fileSize')),
            } for video in video_data['renditions']
        ]
        self._sort_formats(formats)

        thumbnails = [
            {
                'url': 'http://www.nytimes.com/%s' % image['url'],
                'width': int_or_none(image.get('width')),
                'height': int_or_none(image.get('height')),
            } for image in video_data['images']
        ]

        return {
            'id': video_id,
            'title': title,
            'description': description,
            'timestamp': timestamp,
            'uploader': uploader,
            'duration': duration,
            'formats': formats,
            'thumbnails': thumbnails,
        }
