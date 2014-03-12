from __future__ import unicode_literals

import json
import re

from .common import InfoExtractor


class FunnyOrDieIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?funnyordie\.com/(?P<type>embed|videos)/(?P<id>[0-9a-f]+)(?:$|[?#/])'
    _TEST = {
        'url': 'http://www.funnyordie.com/videos/0732f586d7/heart-shaped-box-literal-video-version',
        'file': '0732f586d7.mp4',
        'md5': 'f647e9e90064b53b6e046e75d0241fbd',
        'info_dict': {
            'description': ('Lyrics changed to match the video. Spoken cameo '
                'by Obscurus Lupa (from ThatGuyWithTheGlasses.com). Based on a '
                'concept by Dustin McLean (DustFilms.com). Performed, edited, '
                'and written by David A. Scott.'),
            'title': 'Heart-Shaped Box: Literal Video Version',
        },
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)

        video_id = mobj.group('id')
        webpage = self._download_webpage(url, video_id)

        video_url = self._search_regex(
            [r'type="video/mp4" src="(.*?)"', r'src="([^>]*?)" type=\'video/mp4\''],
            webpage, 'video URL', flags=re.DOTALL)

        if mobj.group('type') == 'embed':
            post_json = self._search_regex(
                r'fb_post\s*=\s*(\{.*?\});', webpage, 'post details')
            post = json.loads(post_json)
            title = post['name']
            description = post.get('description')
            thumbnail = post.get('picture')
        else:
            title = self._og_search_title(webpage)
            description = self._og_search_description(webpage)
            thumbnail = None

        return {
            'id': video_id,
            'url': video_url,
            'ext': 'mp4',
            'title': title,
            'description': description,
            'thumbnail': thumbnail,
        }
