# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor

# Run the following to test
# python test/test_download.py TestDownload.test_Gab


class GabIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?gab\.com/\w+/posts/(?P<id>[0-9]+)+'
    _TESTS = [
        {
            'url': 'https://gab.com/ACT1TV/posts/104450493441154721',
            'md5': '04bbd2146e0afe033eb1cb184f3748ce',
            'info_dict': {
                'id': '104450493441154721',
                'ext': 'mp4',
                'title': 'Bill Blaze on Gab: \'He shoots, he scores and the crowd went wild.... \u2026\' - Gab Social',
                'description': 'Bill Blaze on Gab: \'He shoots, he scores and the crowd went wild.... \u2026\'',
            },
        },
    ]

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')
        webpage = self._download_webpage(url, video_id)
        title = self._html_search_regex(r'<title>(.+?)</title>', webpage, 'title')

        url_result = re.search('https?://(?:www\.)?gab\.com/system/media_attachments/files/[0-9]+/[0-9]+/[0-9]+/original/\w+\.\w+', webpage)
        video_url = url_result.group()

        return {
            'id': video_id,
            'title': title,
            'description': self._og_search_description(webpage),
            'url': video_url,
        }
