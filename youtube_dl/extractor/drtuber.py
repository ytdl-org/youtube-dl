from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import str_to_int


class DrTuberIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?drtuber\.com/video/(?P<id>\d+)/(?P<display_id>[\w-]+)'
    _TEST = {
        'url': 'http://www.drtuber.com/video/1740434/hot-perky-blonde-naked-golf',
        'md5': '93e680cf2536ad0dfb7e74d94a89facd',
        'info_dict': {
            'id': '1740434',
            'display_id': 'hot-perky-blonde-naked-golf',
            'ext': 'mp4',
            'title': 'Hot Perky Blonde Naked Golf',
            'like_count': int,
            'dislike_count': int,
            'comment_count': int,
            'categories': ['Babe', 'Blonde', 'Erotic', 'Outdoor', 'Softcore', 'Solo'],
            'thumbnail': 're:https?://.*\.jpg$',
            'age_limit': 18,
        }
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')
        display_id = mobj.group('display_id')

        webpage = self._download_webpage(url, display_id)

        video_url = self._html_search_regex(
            r'<source src="([^"]+)"', webpage, 'video URL')

        title = self._html_search_regex(
            r'<title>([^<]+)\s*-\s*Free', webpage, 'title')

        thumbnail = self._html_search_regex(
            r'poster="([^"]+)"',
            webpage, 'thumbnail', fatal=False)

        like_count = str_to_int(self._html_search_regex(
            r'<span id="rate_likes">\s*<img[^>]+>\s*<span>([\d,\.]+)</span>',
            webpage, 'like count', fatal=False))
        dislike_count = str_to_int(self._html_search_regex(
            r'<span id="rate_dislikes">\s*<img[^>]+>\s*<span>([\d,\.]+)</span>',
            webpage, 'like count', fatal=False))
        comment_count = str_to_int(self._html_search_regex(
            r'<span class="comments_count">([\d,\.]+)</span>',
            webpage, 'comment count', fatal=False))

        cats_str = self._search_regex(
            r'<span>Categories:</span><div>(.+?)</div>', webpage, 'categories', fatal=False)
        categories = [] if not cats_str else re.findall(r'<a title="([^"]+)"', cats_str)

        return {
            'id': video_id,
            'display_id': display_id,
            'url': video_url,
            'title': title,
            'thumbnail': thumbnail,
            'like_count': like_count,
            'dislike_count': dislike_count,
            'comment_count': comment_count,
            'categories': categories,
            'age_limit': self._rta_search(webpage),
        }
