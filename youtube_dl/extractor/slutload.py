from __future__ import unicode_literals

import re

from .common import InfoExtractor


class SlutloadIE(InfoExtractor):
    _VALID_URL = r'^https?://(?:\w+\.)?slutload\.com/video/[^/]+/(?P<id>[^/]+)/?$'
    _TESTS = [{
        'url': 'http://www.slutload.com/video/virginie-baisee-en-cam/TD73btpBqSxc/',
        'md5': '868309628ba00fd488cf516a113fd717',
        'info_dict': {
            'id': 'TD73btpBqSxc',
            'ext': 'mp4',
            'title': 'virginie baisee en cam',
            'age_limit': 18,
            'thumbnail': r're:https?://.*?\.jpg'
        }
    }, {
        # mobile site
        'url': 'http://mobile.slutload.com/video/masturbation-solo/fviFLmc6kzJ/',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)

        desktop_url = re.sub(r'^(https?://)mobile\.', r'\1', url)
        webpage = self._download_webpage(desktop_url, video_id)

        video_title = self._html_search_regex(r'<h1><strong>([^<]+)</strong>',
                                              webpage, 'title').strip()

        video_url = self._html_search_regex(
            r'(?s)<div id="vidPlayer"\s+data-url="([^"]+)"',
            webpage, 'video URL')
        thumbnail = self._html_search_regex(
            r'(?s)<div id="vidPlayer"\s+.*?previewer-file="([^"]+)"',
            webpage, 'thumbnail', fatal=False)

        return {
            'id': video_id,
            'url': video_url,
            'title': video_title,
            'thumbnail': thumbnail,
            'age_limit': 18
        }
