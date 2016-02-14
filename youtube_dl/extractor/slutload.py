from __future__ import unicode_literals

import re

from .common import InfoExtractor


class SlutloadIE(InfoExtractor):
    _VALID_URL = r'^https?://(?:\w+\.)?slutload\.com/video/[^/]+/(?P<id>[^/]+)/?$'
    _TEST = {
        'url': 'http://www.slutload.com/video/virginie-baisee-en-cam/TD73btpBqSxc/',
        'md5': '0cf531ae8006b530bd9df947a6a0df77',
        'info_dict': {
            'id': 'TD73btpBqSxc',
            'ext': 'mp4',
            'title': 'virginie baisee en cam',
            'age_limit': 18,
            'thumbnail': 're:https?://.*?\.jpg'
        }
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')

        webpage = self._download_webpage(url, video_id)

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
