# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor


class YourUploadIE(InfoExtractor):
    _VALID_URL = r'''(?x)https?://(?:www\.)?
        (?:yourupload\.com/watch|
           embed\.yourupload\.com|
           embed\.yucache\.net
        )/(?P<id>[A-Za-z0-9]+)
        '''
    _TESTS = [
        {
            'url': 'http://yourupload.com/watch/14i14h',
            'md5': '5e2c63385454c557f97c4c4131a393cd',
            'info_dict': {
                'id': '14i14h',
                'ext': 'mp4',
                'title': 'BigBuckBunny_320x180.mp4',
                'thumbnail': 're:^https?://.*\.jpe?g',
            }
        },
        {
            'url': 'http://embed.yourupload.com/14i14h',
            'only_matching': True,
        },
        {
            'url': 'http://embed.yucache.net/14i14h?client_file_id=803349',
            'only_matching': True,
        },
    ]

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')

        embed_url = 'http://embed.yucache.net/{0:}'.format(video_id)
        webpage = self._download_webpage(embed_url, video_id)

        title = self._og_search_title(webpage)
        thumbnail = self._og_search_thumbnail(webpage)
        video_url = self._og_search_video_url(webpage)

        formats = [{
            'format_id': 'sd',
            'url': video_url,
        }]

        return {
            'id': video_id,
            'title': title,
            'formats': formats,
            'thumbnail': thumbnail,
            'http_headers': {
                'Referer': embed_url,
            },
        }
