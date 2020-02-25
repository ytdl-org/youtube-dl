# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import determine_ext

import re


class AirVuzIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?airvuz\.com/video/(?P<display_id>.+)\?id=(?P<id>.+)'
    _TEST = {
        'url': 'https://www.airvuz.com/video/An-Imaginary-World?id=599e85c49282a717c50f2f7a',
        'info_dict': {
            'id': '599e85c49282a717c50f2f7a',
            'display_id': 'An-Imaginary-World',
            'title': 'md5:7fc56270e7a70fa81a5935b72eacbe29',
            'ext': 'mp4',
            'thumbnail': r're:^https?://.*\.jpg$',
        },
    }

    def _real_extract(self, url):
        groups = re.match(self._VALID_URL, url)
        video_id = groups.group('id')
        display_id = groups.group('display_id')

        webpage = self._download_webpage(url, video_id)

        title = self._og_search_title(webpage)
        thumbnail = self._og_search_thumbnail(webpage)
        description = self._og_search_description(webpage)
        uploader = self._html_search_regex(r'class=(?:\'img-circle\'|"img-circle"|img-circle)[^>]+?alt=(?:"([^"]+?)"|\'([^\']+?)\'|([^\s"\'=<>`]+))', webpage, 'uploader', fatal=False) or self._html_search_regex(r'https?://(?:www\.)?airvuz\.com/user/([^>]*)', webpage, 'uploader', fatal=False)

        video_url = self._html_search_regex(r'<meta[^>]+?(?:name|property)=(?:\'og:video:url\'|"og:video:url"|og:video:url)[^>]+?content=(?:"([^"]+?)"|\'([^\']+?)\'|([^\s"\'=<>`]+))', webpage, 'video_url')
        ext = determine_ext(video_url)

        return {
            'id': video_id,
            'display_id': display_id,
            'title': title,
            'url': video_url,
            'ext': ext,
            'thumbnail': thumbnail,
            'description': description,
            'uploader': uploader,
        }
