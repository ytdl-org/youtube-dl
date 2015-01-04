# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor


class StreetfireIE(InfoExtractor):
    _VALID_URL = r'http?://(?:www\.)?streetfire\.net/video/[a-zA-Z0-9\-]*_(?P<id>[0-9]+).htm'
    _TEST = {
        'url': 'http://www.streetfire.net/video/top-gear-bolivia-special-season-14-episode-6_1994638.htm',
        'md5': '5ea46aa8e6063a6f2d1164e9b6986deb',
        'info_dict': {
            'id': '1994638',
            'ext': 'swf',
            'title': 'Top Gear Bolivia Special (Season 14 Episode 6)',
            'description': ('The 3 have to buy a car with 4WD and set out on an adventure in rain forests,'
                            ' deserts, volcanoes and much more. Run-time: over an hour. No SIARPC or test'
                            ' runs. No copyright intended. Viewing purposes only. Property of the BBC.')
            # 'thumbnail': ''
            # 'thumbnail': 're:^https?://.*\.jpg$',
            # TODO more properties, either as:
            # * A value
            # * MD5 checksum; start the string with md5:
            # * A regular expression; start the string with re:
            # * Any Python type (for example int or float)
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        # print url
        webpage = self._download_webpage(url, video_id)

        # TODO more code goes here, for example ...
        title = self._og_search_title(webpage, default=None) or self._html_search_regex(r'<title>(.*?)</title>', webpage, 'title')

        return {
            'id': video_id,
            'title': title,
            'description': self._og_search_description(webpage),
            'url': self._og_search_video_url(webpage),
            # TODO more properties (see youtube_dl/extractor/common.py)
        }