# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor


class NimsesIE(InfoExtractor):
    _UUID_RE = r'[\da-fA-F]{8}-[\da-fA-F]{4}-[\da-fA-F]{4}-[\da-fA-F]{4}-[\da-fA-F]{12}'
    _VALID_URL = r'https?://web\.nimses\.com/post/(?P<id>%s)' % _UUID_RE
    _TEST = {
        'url': 'https://web.nimses.com/post/f4227748-e7ab-4b4d-906e-834234b3d921',
        'md5': '3316c2c4377d73cedf7b9c844fcc3144',
        'info_dict': {
            'id': 'f4227748-e7ab-4b4d-906e-834234b3d921',
            'ext': 'mp4',
            'title': 'Video by pewdiepie',
            'thumbnail': r're:^https?://.*\.jpg$',
            'description': 'Welcome',
            'uploader': 'pewdiepie',
            'uploader_id': '5384bee1-ab81-4370-b996-fc62b1e561aa',
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        api_info = self._download_json('https://web.nimses.com/api/feed/post?id=' + video_id, video_id)
        uploader_id = api_info.get('profileId')
        uploader = api_info.get('userName')
        video_url = api_info['photo']
        description = api_info.get('text')
        likes = api_info.get('nimsCount')
        comments = api_info.get('commentsCount')
        views = api_info.get('viewsCount')
        title = api_info['title']  # note: can be empty
        if title == '':
            title = 'Video by ' + uploader
        thumbnail = api_info.get('urlThumbnail')

        return {
            'id': video_id,
            'title': title,
            'description': description,
            'uploader_id': uploader_id,
            'channel_id': uploader_id,
            'uploader': uploader,
            'channel': uploader,
            'creator': uploader,
            'url': video_url,
            'description': description,
            'like_count': likes,
            'comment_count': comments,
            'view_count': views,
            'title': title,
            'thumbnail': thumbnail,
        }
