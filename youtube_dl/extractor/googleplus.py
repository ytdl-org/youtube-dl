# coding: utf-8
from __future__ import unicode_literals

import datetime
import re

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
)


class GooglePlusIE(InfoExtractor):
    IE_DESC = 'Google Plus'
    _VALID_URL = r'https://plus\.google\.com/(?:[^/]+/)*?posts/(?P<id>\w+)'
    IE_NAME = 'plus.google'
    _TEST = {
        'url': 'https://plus.google.com/u/0/108897254135232129896/posts/ZButuJc6CtH',
        'info_dict': {
            'id': 'ZButuJc6CtH',
            'ext': 'flv',
            'upload_date': '20120613',
            'uploader': '井上ヨシマサ',
            'title': '嘆きの天使 降臨',
        }
    }

    def _real_extract(self, url):
        # Extract id from URL
        mobj = re.match(self._VALID_URL, url)

        video_id = mobj.group('id')

        # Step 1, Retrieve post webpage to extract further information
        webpage = self._download_webpage(url, video_id, 'Downloading entry webpage')

        self.report_extraction(video_id)

        # Extract update date
        upload_date = self._html_search_regex(
            r'''(?x)<a.+?class="o-U-s\s[^"]+"\s+style="display:\s*none"\s*>
                    ([0-9]{4}-[0-9]{2}-[0-9]{2})</a>''',
            webpage, 'upload date', fatal=False, flags=re.VERBOSE)
        if upload_date:
            # Convert timestring to a format suitable for filename
            upload_date = datetime.datetime.strptime(upload_date, "%Y-%m-%d")
            upload_date = upload_date.strftime('%Y%m%d')

        # Extract uploader
        uploader = self._html_search_regex(r'rel\="author".*?>(.*?)</a>',
            webpage, 'uploader', fatal=False)

        # Extract title
        # Get the first line for title
        video_title = self._html_search_regex(r'<meta name\=\"Description\" content\=\"(.*?)[\n<"]',
            webpage, 'title', default='NA')

        # Step 2, Simulate clicking the image box to launch video
        DOMAIN = 'https://plus.google.com/'
        video_page = self._search_regex(r'<a href="((?:%s)?photos/.*?)"' % re.escape(DOMAIN),
            webpage, 'video page URL')
        if not video_page.startswith(DOMAIN):
            video_page = DOMAIN + video_page

        webpage = self._download_webpage(video_page, video_id, 'Downloading video page')

        # Extract video links all sizes
        pattern = r'\d+,\d+,(\d+),"(http\://redirector\.googlevideo\.com.*?)"'
        mobj = re.findall(pattern, webpage)
        if len(mobj) == 0:
            raise ExtractorError('Unable to extract video links')

        # Sort in resolution
        links = sorted(mobj)

        # Choose the lowest of the sort, i.e. highest resolution
        video_url = links[-1]
        # Only get the url. The resolution part in the tuple has no use anymore
        video_url = video_url[-1]
        # Treat escaped \u0026 style hex
        try:
            video_url = video_url.decode("unicode_escape")
        except AttributeError: # Python 3
            video_url = bytes(video_url, 'ascii').decode('unicode-escape')

        return {
            'id': video_id,
            'url': video_url,
            'uploader': uploader,
            'upload_date': upload_date,
            'title': video_title,
            'ext': 'flv',
        }
