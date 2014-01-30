from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    compat_urllib_parse,
)

class MalemotionIE(InfoExtractor):
    _VALID_URL = r'^(?:https?://)?malemotion\.com/video/(.+?)\.(?P<id>.+?)(#|$)'
    _TEST = {
        'url': 'http://malemotion.com/video/bien-dur.10ew',
        'file': '10ew.mp4',
        'md5': 'b3cc49f953b107e4a363cdff07d100ce',
        'info_dict': {
            "title": "Bien dur",
            "age_limit": 18,
        },
        'skip': 'This video has been deleted.'
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group("id")

        webpage = self._download_webpage(url, video_id)

        self.report_extraction(video_id)

        # Extract video URL
        video_url = compat_urllib_parse.unquote(
            self._search_regex(r'<source type="video/mp4" src="(.+?)"', webpage, 'video URL'))

        # Extract title
        video_title = self._html_search_regex(
            r'<title>(.*?)</title', webpage, 'title')

        # Extract video thumbnail
        video_thumbnail = self._search_regex(
            r'<video .+?poster="(.+?)"', webpage, 'thumbnail', fatal=False)

        formats = [{
            'url': video_url,
            'ext': 'mp4',
            'format_id': 'mp4',
            'preference': 1,
        }]

        return {
            'id': video_id,
            'formats': formats,
            'uploader': None,
            'upload_date': None,
            'title': video_title,
            'thumbnail': video_thumbnail,
            'description': None,
            'age_limit': 18,
        }
