# coding: utf-8
from __future__ import unicode_literals

import re
import codecs

from .common import InfoExtractor
from ..utils import unified_strdate


class GooglePlusIE(InfoExtractor):
    IE_DESC = 'Google Plus'
    _VALID_URL = r'https?://plus\.google\.com/(?:[^/]+/)*?posts/(?P<id>\w+)'
    IE_NAME = 'plus.google'
    _TEST = {
        'url': 'https://plus.google.com/u/0/108897254135232129896/posts/ZButuJc6CtH',
        'info_dict': {
            'id': 'ZButuJc6CtH',
            'ext': 'flv',
            'title': '嘆きの天使 降臨',
            'upload_date': '20120613',
            'uploader': '井上ヨシマサ',
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)

        # Step 1, Retrieve post webpage to extract further information
        webpage = self._download_webpage(url, video_id, 'Downloading entry webpage')

        title = self._og_search_description(webpage).splitlines()[0]
        upload_date = unified_strdate(self._html_search_regex(
            r'''(?x)<a.+?class="o-U-s\s[^"]+"\s+style="display:\s*none"\s*>
                    ([0-9]{4}-[0-9]{2}-[0-9]{2})</a>''',
            webpage, 'upload date', fatal=False, flags=re.VERBOSE))
        uploader = self._html_search_regex(
            r'rel="author".*?>(.*?)</a>', webpage, 'uploader', fatal=False)

        # Step 2, Simulate clicking the image box to launch video
        DOMAIN = 'https://plus.google.com/'
        video_page = self._search_regex(
            r'<a href="((?:%s)?photos/.*?)"' % re.escape(DOMAIN),
            webpage, 'video page URL')
        if not video_page.startswith(DOMAIN):
            video_page = DOMAIN + video_page

        webpage = self._download_webpage(video_page, video_id, 'Downloading video page')

        def unicode_escape(s):
            decoder = codecs.getdecoder('unicode_escape')
            return re.sub(
                r'\\u[0-9a-fA-F]{4,}',
                lambda m: decoder(m.group(0))[0],
                s)

        # Extract video links all sizes
        formats = [{
            'url': unicode_escape(video_url),
            'ext': 'flv',
            'width': int(width),
            'height': int(height),
        } for width, height, video_url in re.findall(
            r'\d+,(\d+),(\d+),"(https?://[^.]+\.googleusercontent\.com.*?)"', webpage)]
        self._sort_formats(formats)

        return {
            'id': video_id,
            'title': title,
            'uploader': uploader,
            'upload_date': upload_date,
            'formats': formats,
        }
