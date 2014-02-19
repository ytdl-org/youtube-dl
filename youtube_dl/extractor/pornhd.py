from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import compat_urllib_parse


class PornHdIE(InfoExtractor):
    _VALID_URL = r'(?:http://)?(?:www\.)?pornhd\.com/(?:[a-z]{2,4}/)?videos/(?P<video_id>[0-9]+)/(?P<video_title>.+)'
    _TEST = {
        'url': 'http://www.pornhd.com/videos/1962/sierra-day-gets-his-cum-all-over-herself-hd-porn-video',
        'file': '1962.flv',
        'md5': '35272469887dca97abd30abecc6cdf75',
        'info_dict': {
            "title": "sierra-day-gets-his-cum-all-over-herself-hd-porn-video",
            "age_limit": 18,
        }
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)

        video_id = mobj.group('video_id')
        video_title = mobj.group('video_title')

        webpage = self._download_webpage(url, video_id)

        next_url = self._html_search_regex(
            r'&hd=(http.+?)&', webpage, 'video URL')
        next_url = compat_urllib_parse.unquote(next_url)

        video_url = self._download_webpage(
            next_url, video_id, note='Retrieving video URL',
            errnote='Could not retrieve video URL')
        age_limit = 18

        return {
            'id': video_id,
            'url': video_url,
            'ext': 'flv',
            'title': video_title,
            'age_limit': age_limit,
        }
