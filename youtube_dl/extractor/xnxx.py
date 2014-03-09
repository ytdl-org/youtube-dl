# encoding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    compat_urllib_parse,
)


class XNXXIE(InfoExtractor):
    _VALID_URL = r'^https?://(?:video|www)\.xnxx\.com/video(?P<id>[0-9]+)/(.*)'
    _TEST = {
        'url': 'http://video.xnxx.com/video1135332/lida_naked_funny_actress_5_',
        'md5': '0831677e2b4761795f68d417e0b7b445',
        'info_dict': {
            'id': '1135332',
            'ext': 'flv',
            'title': 'lida » Naked Funny Actress  (5)',
            'age_limit': 18,
        }
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')

        # Get webpage content
        webpage = self._download_webpage(url, video_id)

        video_url = self._search_regex(r'flv_url=(.*?)&amp;',
            webpage, 'video URL')
        video_url = compat_urllib_parse.unquote(video_url)

        video_title = self._html_search_regex(r'<title>(.*?)\s+-\s+XNXX.COM',
            webpage, 'title')

        video_thumbnail = self._search_regex(r'url_bigthumb=(.*?)&amp;',
            webpage, 'thumbnail', fatal=False)

        return {
            'id': video_id,
            'url': video_url,
            'title': video_title,
            'ext': 'flv',
            'thumbnail': video_thumbnail,
            'age_limit': 18,
        }
