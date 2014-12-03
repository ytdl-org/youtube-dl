# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor

import re


class TheOfficeIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?theoffice\.so/(?P<id>[0-9]{4}).html$'
    _TESTS = [
        {
            'url': 'http://theoffice.so/0304.html',
            'md5': '0abec1d2d91d75b2f331fc426f7fb0d4',
            'info_dict': {
                'id': '0304',
                'ext': 'mp4',
                'title': 'Episode 4: Grief Counseling',
            },
        },
        {
            'url': 'http://theoffice.so/0607.html',
            'md5': '1b2d4dab2e1af3f855c5f55a63a1ba70',
            'info_dict': {
                'id': '0607',
                'ext': 'mp4',
                'title': 'Episode 7: The Lover',
            }
        },
    ]

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')
        info_page = self._download_webpage('http://www.theoffice.so/index.html', video_id, 'Requesting video overview page')

        # look which link on the info page refers to our video
        pattern = r'<a href="../'+video_id+'.html">(.*?)</a>'
        title = self._html_search_regex(pattern, info_page, 'title')

        # the videos are hosted statically on a single server
        url = 'http://94.242.228.164/T' + video_id + '.mp4'
        return {
            'id': video_id,
            'title': title,
            'url': url,
            'ext': 'mp4'
        }
