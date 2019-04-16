# coding: utf-8
from __future__ import unicode_literals
import re
from .common import InfoExtractor


class BajeczkiIE(InfoExtractor):
    _VALID_URL = r'http?://(?:www\.)?bajeczki\.org/(?P<id>.*)'
    _TEST = {
        'url': 'http://bajeczki.org/psi-patrol/pieski-ratuja-przyjaciol-ksiezniczki/',
        'md5': '01f72e7e641448785db6a9bd77a94b31',
        'info_dict': {
            'id': 'psi-patrol/pieski-ratuja-przyjaciol-ksiezniczki/',
            'ext': 'mp4',
            'title': 'Psi Patrol - Psia misja: Pieski ratują przyjaciół księżniczki | Bajki na Bajeczki.org',
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
        # print (webpage)
        # TODO more code goes here, for example ...
        title = self._html_search_regex(r'<title>(.+?)</title>', webpage, 'title')
        test = self._search_regex(r'(http.*\.mp4)', webpage, 'url')
        print(test)
        url = re.sub('\\\\', '', test)
        print(url)

        return {
            'id': video_id,
            'title': title,
            'url': url,
            # 'description': self._og_search_description(webpage),
            # 'uploader': self._search_regex(r'<div[^>]+id="uploader"[^>]*>([^<]+)<', webpage, 'uploader', fatal=False),
            # TODO more properties (see youtube_dl/extractor/common.py)
        }
