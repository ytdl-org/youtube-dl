from __future__ import unicode_literals

import re

from .common import InfoExtractor


class DrTuberIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?drtuber\.com/video/(?P<id>\d+)/(?P<title_dash>[\w-]+)'
    _TEST = {
        'url': 'http://www.drtuber.com/video/1740434/hot-perky-blonde-naked-golf',
        'md5': '93e680cf2536ad0dfb7e74d94a89facd',
        'info_dict': {
            'id': '1740434',
            'ext': 'mp4',
            'title': 'Hot Perky Blonde Naked Golf',
            'categories': list,  # NSFW
            'thumbnail': 're:https?://.*\.jpg$',
            'age_limit': 18,
        }
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')

        webpage = self._download_webpage(url, video_id)

        video_url = self._html_search_regex(
            r'<source src="([^"]+)"', webpage, 'video URL')

        title = self._html_search_regex(
            r'<title>([^<]+)\s*-\s*Free', webpage, 'title')

        thumbnail = self._html_search_regex(
            r'poster="([^"]+)"',
            webpage, 'thumbnail', fatal=False)

        cats_str = self._html_search_regex(
            r'<meta name="keywords" content="([^"]+)"', webpage, 'categories', fatal=False)
        categories = None if cats_str is None else cats_str.split(' ')

        return {
            'id': video_id,
            'url': video_url,
            'title': title,
            'thumbnail': thumbnail,
            'categories': categories,
            'age_limit': self._rta_search(webpage),
        }
