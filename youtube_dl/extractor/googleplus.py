# coding: utf-8

import datetime
import re

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
)


class GooglePlusIE(InfoExtractor):
    IE_DESC = u'Google Plus'
    _VALID_URL = r'(?:https://)?plus\.google\.com/(?:[^/]+/)*?posts/(\w+)'
    IE_NAME = u'plus.google'
    _TEST = {
        u"url": u"https://plus.google.com/u/0/108897254135232129896/posts/ZButuJc6CtH",
        u"file": u"ZButuJc6CtH.flv",
        u"info_dict": {
            u"upload_date": u"20120613",
            u"uploader": u"井上ヨシマサ",
            u"title": u"嘆きの天使 降臨"
        }
    }

    def _real_extract(self, url):
        # Extract id from URL
        mobj = re.match(self._VALID_URL, url)
        if mobj is None:
            raise ExtractorError(u'Invalid URL: %s' % url)

        post_url = mobj.group(0)
        video_id = mobj.group(1)

        video_extension = 'flv'

        # Step 1, Retrieve post webpage to extract further information
        webpage = self._download_webpage(post_url, video_id, u'Downloading entry webpage')

        self.report_extraction(video_id)

        # Extract update date
        upload_date = self._html_search_regex(
            r'''(?x)<a.+?class="o-U-s\s[^"]+"\s+style="display:\s*none"\s*>
                    ([0-9]{4}-[0-9]{2}-[0-9]{2})</a>''',
            webpage, u'upload date', fatal=False, flags=re.VERBOSE)
        if upload_date:
            # Convert timestring to a format suitable for filename
            upload_date = datetime.datetime.strptime(upload_date, "%Y-%m-%d")
            upload_date = upload_date.strftime('%Y%m%d')

        # Extract uploader
        uploader = self._html_search_regex(r'rel\="author".*?>(.*?)</a>',
            webpage, u'uploader', fatal=False)

        # Extract title
        # Get the first line for title
        video_title = self._html_search_regex(r'<meta name\=\"Description\" content\=\"(.*?)[\n<"]',
            webpage, 'title', default=u'NA')

        # Step 2, Simulate clicking the image box to launch video
        DOMAIN = 'https://plus.google.com/'
        video_page = self._search_regex(r'<a href="((?:%s)?photos/.*?)"' % re.escape(DOMAIN),
            webpage, u'video page URL')
        if not video_page.startswith(DOMAIN):
            video_page = DOMAIN + video_page

        webpage = self._download_webpage(video_page, video_id, u'Downloading video page')

        # Extract video links on video page
        """Extract video links of all sizes"""
        pattern = r'\d+,\d+,(\d+),"(http\://redirector\.googlevideo\.com.*?)"'
        mobj = re.findall(pattern, webpage)
        if len(mobj) == 0:
            raise ExtractorError(u'Unable to extract video links')

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


        return [{
            'id':       video_id,
            'url':      video_url,
            'uploader': uploader,
            'upload_date':  upload_date,
            'title':    video_title,
            'ext':      video_extension,
        }]
