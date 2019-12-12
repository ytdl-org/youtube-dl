# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor


class GamerDVRIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?gamerdvr\.com/gamer/\S+/video/(?P<id>\d+)'
    _TEST = {
        'url': 'https://gamerdvr.com/gamer/videogamer3/video/82254474',
        'md5': 'TODO: md5 sum of the first 10241 bytes of the video file (use --test)',
        'info_dict': {
            'id': '42',
            'ext': 'mp4',
            'title': 'Video title goes here',
            'thumbnail': r're:^https?://.*\.jpg$',
            # TODO more properties, either as:
            # * A value
            # * MD5 checksum; start the string with md5:
            # * A regular expression; start the string with re:
            # * Any Python type (for example int or float)
        }
    }

    def _real_extract(self, url):
        # video_id = self._match_id(url)
        # webpage = self._download_webpage(url, video_id)

        # # TODO more code goes here, for example ...
        # title = self._html_search_regex(r'<h1>(.+?)</h1>', webpage, 'title')

        return {
            'id': 'id goes here',
            'title': 'title goes here',
            'description': 'desc goes here',
            'uploader': 'uploader goes here',
            # TODO more properties (see youtube_dl/extractor/common.py)
        }