from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import parse_iso8601


class NYTimesIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?nytimes\.com/video/(?:[^/]+/)+(?P<id>\d+)'

    _TEST = {
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
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')

        video_data = self._download_json(
            'http://www.nytimes.com/svc/video/api/v2/video/%s' % video_id, video_id, 'Downloading video JSON')

        title = video_data['headline']
        description = video_data['summary']
        duration = video_data['duration'] / 1000.0

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
                'format_id': video['type'],
                'vcodec': video['video_codec'],
                'width': video['width'],
                'height': video['height'],
                'filesize': get_file_size(video['fileSize']),
            } for video in video_data['renditions']
        ]
        self._sort_formats(formats)

        thumbnails = [
            {
                'url': 'http://www.nytimes.com/%s' % image['url'],
                'resolution': '%dx%d' % (image['width'], image['height']),
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
