from __future__ import unicode_literals

import json
import re

from .common import InfoExtractor


class FunnyOrDieIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?funnyordie\.com/(?P<type>embed|videos)/(?P<id>[0-9a-f]+)(?:$|[?#/])'
    _TESTS = [{
        'url': 'http://www.funnyordie.com/videos/0732f586d7/heart-shaped-box-literal-video-version',
        'md5': 'f647e9e90064b53b6e046e75d0241fbd',
        'info_dict': {
            'id': '0732f586d7',
            'ext': 'mp4',
            'title': 'Heart-Shaped Box: Literal Video Version',
            'description': 'md5:ea09a01bc9a1c46d9ab696c01747c338',
            'thumbnail': 're:^http:.*\.jpg$',
        },
    }, {
        'url': 'http://www.funnyordie.com/embed/e402820827',
        'md5': '0e0c5a7bf45c52b95cd16aa7f28be0b6',
        'info_dict': {
            'id': 'e402820827',
            'ext': 'mp4',
            'title': 'Please Use This Song (Jon Lajoie)',
            'description': 'md5:2ed27d364f5a805a6dba199faaf6681d',
            'thumbnail': 're:^http:.*\.jpg$',
        },
    }]

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)

        video_id = mobj.group('id')
        webpage = self._download_webpage(url, video_id)

        video_url = self._search_regex(
            [r'type="video/mp4" src="(.*?)"', r'src="([^>]*?)" type=\'video/mp4\''],
            webpage, 'video URL', flags=re.DOTALL)

        post_json = self._search_regex(
            r'fb_post\s*=\s*(\{.*?\});', webpage, 'post details')
        post = json.loads(post_json)

        return {
            'id': video_id,
            'url': video_url,
            'ext': 'mp4',
            'title': post['name'],
            'description': post.get('description'),
            'thumbnail': post.get('picture'),
        }
