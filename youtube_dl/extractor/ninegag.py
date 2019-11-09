from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    determine_ext,
    ExtractorError
)


class NineGagIE(InfoExtractor):
    IE_NAME = '9gag'
    _VALID_URL = r'https?://(?:www\.)?9gag\.com/gag/(?P<id>[a-zA-Z0-9]+)'

    _TESTS = [{
        'url': 'https://9gag.com/gag/an5Qz5b',
        'info_dict': {
            'id': 'an5Qz5b',
            'ext': 'webm',
            'title': 'Dogs playing tetherball',
            'upload_date': '20191108',
            'timestamp': 1573243994,
            'age_limit': 0,
            'categories': [
                'Wholesome'
            ],
            'tags': [
                'Dog'
            ]
        }
    }, {
        'url': 'https://9gag.com/gag/ae5Ag7B',
        'info_dict': {
            'id': 'ae5Ag7B',
            'ext': 'webm',
            'title': 'Capybara Agility Training',
            'upload_date': '20191108',
            'timestamp': 1573237208,
            'age_limit': 0,
            'categories': [
                'Awesome'
            ],
            'tags': [
                'Weimaraner',
                'American Pit Bull Terrier'
            ]
        }
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)
        rawJsonData = self._search_regex(
            r'window._config\s*=\s*JSON.parse\("({.+?})"\);',
            webpage,
            'data')
        rawJsonData = rawJsonData.replace('\\"', '"').replace('\\\\/', '/')
        data = self._parse_json(rawJsonData, video_id)['data']['post']

        if data['type'] != 'Animated':
            raise ExtractorError('The given url does not contain a video', expected=True)

        duration = None
        formats = []
        thumbnails = []
        for key in data['images']:
            image = data['images'][key]
            if 'duration' in image and duration is None:
                duration = image['duration']
            url = image['url']
            ext = determine_ext(url)
            if ext == 'jpg' or ext == 'png':
                thumbnail = {
                    'url': url,
                    'width': image['width'],
                    'height': image['height']
                }
                thumbnails.append(thumbnail)
            elif ext == 'webm' or ext == 'mp4':
                formats.append({
                    'format_id': re.sub(r'.*_([^\.]+).(.*)', r'\1_\2', url),
                    'ext': ext,
                    'url': url,
                    'width': image['width'],
                    'height': image['height']
                })
        section = re.sub(r'\\[^\\]{5}', '', data['postSection']['name'])
        tags = None
        if 'tags' in data:
            tags = []
            for tag in data['tags']:
                tags.append(tag['key'])

        return {
            'id': video_id,
            'title': data['title'],
            'timestamp': data['creationTs'],
            'duration': duration,
            'formats': formats,
            'thumbnails': thumbnails,
            'like_count': data['upVoteCount'],
            'dislike_count': data['downVoteCount'],
            'comment_count': data['commentsCount'],
            'age_limit': data['nsfw'] * 18,
            'categories': [section],
            'tags': tags,
            'is_live': False
        }
