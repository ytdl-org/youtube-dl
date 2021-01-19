from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    determine_ext,
    url_or_none,
    int_or_none,
    float_or_none,
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

    _EXTERNAL_VIDEO_PROVIDERS = {
        'Youtube': 'https://youtube.com/watch?v=%s'
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)
        rawJsonData = self._search_regex(
            r'window._config\s*=\s*JSON.parse\(["\']({.+?})["\']\);',
            webpage,
            'data')
        rawJsonData = rawJsonData.replace('\\"', '"').replace('\\\\/', '/')
        data = self._parse_json(rawJsonData, video_id)['data']['post']

        if data['type'] == 'Video':
            vid = data['video']['id']
            ie_key = data['video']['source'].capitalize()
            return {
                '_type': 'url_transparent',
                'url': self._EXTERNAL_VIDEO_PROVIDERS[ie_key] % vid,
                'ie_key': ie_key,
                'id': vid,
                'duration': data['video'].get('duration'),
                'start_time': data['video'].get('startTs')
            }

        if data['type'] == 'EmbedVideo':
            vid = data['video']['id']
            ie_key = data['video']['source'].capitalize()
            return {
                '_type': 'url_transparent',
                'url': data['video']['embedUrl'],
                #'ie_key': vid,
                'start_time': data['video'].get('startTs')
            }

        if data['type'] != 'Animated':
            raise ExtractorError(
                'The given url does not contain a video',
                expected=True)

        duration = None
        formats = []
        thumbnails = []
        for key in data['images']:
            image = data['images'][key]
            if 'duration' in image and duration is None:
                duration = int_or_none(image['duration'])
            url = url_or_none(image.get('url'))
            if url == None:
                continue
            ext = determine_ext(url)
            if ext == 'jpg' or ext == 'png':
                thumbnail = {
                    'url': url,
                    'width': float_or_none(image.get('width')),
                    'height': float_or_none(image.get('height'))
                }
                thumbnails.append(thumbnail)
            elif ext == 'webm' or ext == 'mp4':
                formats.append({
                    'format_id': re.sub(r'.*_([^\.]+).(.*)', r'\1_\2', url),
                    'ext': ext,
                    'url': url,
                    'width': float_or_none(image.get('width')),
                    'height': float_or_none(image.get('height'))
                })
        section = None
        postSection = data.get('postSection')
        if postSection != None and 'name' in postSection:
            section = re.sub(r'\\[^\\]{5}', '', postSection['name'])
        age_limit = int_or_none(data.get('nsfw'))
        if age_limit != None:
            age_limit = age_limit * 18
        tags = None
        if 'tags' in data:
            tags = []
            for tag in data.get('tags') or []:
                tags.append(tag.get('key'))

        return {
            'id': video_id,
            'title': data['title'],
            'timestamp': int_or_none(data.get('creationTs')),
            'duration': duration,
            'formats': formats,
            'thumbnails': thumbnails,
            'like_count': int_or_none(data.get('upVoteCount')),
            'dislike_count': int_or_none(data.get('downVoteCount')),
            'comment_count': int_or_none(data.get('commentsCount')),
            'age_limit': age_limit,
            'categories': [section],
            'tags': tags,
            'is_live': False
        }
