# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor


class VolAtIE(InfoExtractor):
    print("wtf")
    _VALID_URL = r'https?://(?:www\.)?vol\.at/(?P<id>[0-9]+)'
    _TEST = {
        'url': 'http://www.vol.at/blue-man-group/5593454',
        'md5': 'TODO: md5 sum of the first 10241 bytes of the video file (use --test)',
        'info_dict': {
            'id': '5593454',
            'ext': 'mp4',
            'title': '"Blau ist mysteriös": Die Blue Man Group im Interview',
            'thumbnail': r're:^https?://.*\.jpg$',
            # TODO more properties, either as:
            # * A value
            # * MD5 checksum; start the string with md5:
            # * A regular expression; start the string with re:
            # * Any Python type (for example int or float)
        }
    }

    def _real_extract(self, url):
        print("hello test")
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
