from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    parse_iso8601,
    str_to_int,
)


class CrackedIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?cracked\.com/video_(?P<id>\d+)_[\da-z-]+\.html'
    _TEST = {
        'url': 'http://www.cracked.com/video_19006_4-plot-holes-you-didnt-notice-in-your-favorite-movies.html',
        'md5': '4b29a5eeec292cd5eca6388c7558db9e',
        'info_dict': {
            'id': '19006',
            'ext': 'mp4',
            'title': '4 Plot Holes You Didn\'t Notice in Your Favorite Movies',
            'description': 'md5:3b909e752661db86007d10e5ec2df769',
            'timestamp': 1405659600,
            'upload_date': '20140718',
        }
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')

        webpage = self._download_webpage(url, video_id)

        video_url = self._html_search_regex(
            [r'var\s+CK_vidSrc\s*=\s*"([^"]+)"', r'<video\s+src="([^"]+)"'], webpage, 'video URL')

        title = self._og_search_title(webpage)
        description = self._og_search_description(webpage)

        timestamp = self._html_search_regex(r'<time datetime="([^"]+)"', webpage, 'upload date', fatal=False)
        if timestamp:
            timestamp = parse_iso8601(timestamp[:-6])

        view_count = str_to_int(self._html_search_regex(
            r'<span class="views" id="viewCounts">([\d,\.]+) Views</span>', webpage, 'view count', fatal=False))
        comment_count = str_to_int(self._html_search_regex(
            r'<span id="commentCounts">([\d,\.]+)</span>', webpage, 'comment count', fatal=False))

        m = re.search(r'_(?P<width>\d+)X(?P<height>\d+)\.mp4$', video_url)
        if m:
            width = int(m.group('width'))
            height = int(m.group('height'))
        else:
            width = height = None

        return {
            'id': video_id,
            'url': video_url,
            'title': title,
            'description': description,
            'timestamp': timestamp,
            'view_count': view_count,
            'comment_count': comment_count,
            'height': height,
            'width': width,
        }
