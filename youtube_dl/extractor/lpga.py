# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor


class YourExtractorIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?lpga\.com/watch/(?P<id>[0-9]+)'
    _TEST = {
        'url': 'http://www.lpga.com/videos/brooke-henderson-talks-about-solid-back-9-after-opening-round-of-2016-voa-texas-shootout',
        'md5': '0d3b32a11fdb2ab46f66be2932ea10a68790aa1d',
        'info_dict': {
            'id': '42',
            'ext': 'mp4',
            'title': 'Video title goes here',
            'thumbnail': 're:^https?://.*\.jpg$',
            # TODO more properties, either as:
            # * A value
            # * MD5 checksum; start the string with md5:
            # * A regular expression; start the string with re:
            # * Any Python type (for example int or float)
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        # TODO more code goes here, for example ...
        title = self._html_search_regex(r'<h1>(.+?)</h1>', webpage, 'title')

        return {
            'id': video_id,
            'title': title,
            'description': self._og_search_description(webpage),
            'uploader': self._search_regex(r'<div[^>]+id="uploader"[^>]*>([^<]+)<', webpage, 'uploader', fatal=False),
            # TODO more properties (see youtube_dl/extractor/common.py)
        }
