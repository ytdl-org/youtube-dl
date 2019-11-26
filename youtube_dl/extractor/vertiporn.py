# coding: utf-8
from __future__ import unicode_literals
from urlparse import urlparse
from .common import InfoExtractor


class VertiPornIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?vertiporn\.com/video/(?P<id>[0-9]+)/(?P<title>)'
    _TEST = {
        'url': 'https://www.vertiporn.com/video/83/blowjob-teen-pov',
        'md5': '3c154a5183f3f04b516e20600ff5337c',
        'info_dict': {
            'id': '83',
            'ext': 'mp4',
            'title': 'Blowjob Teen POV - VertiPorn.com',
            # 'thumbnail': r're:^https?://.*\.jpg$',
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
        title = self._html_search_regex(r'<title>(.+?)</title>', webpage, 'title')
        video_string = self._html_search_regex(r'.*<source\t*src=\"(.*\.mp4)\".*>', webpage, 'video')
        video_url = urlparse(url).scheme + "://" + urlparse(url).netloc + video_string.strip('..')

        return {
            'id': video_id,
            'title': title,
            'ext': 'mp4',
            'url': video_url,

            # 'description': self._og_search_description(webpage),
            # 'uploader': self._search_regex(r'<div[^>]+id="uploader"[^>]*>([^<]+)<', webpage, 'uploader', fatal=False),
            # TODO more properties (see youtube_dl/extractor/common.py)
        }
