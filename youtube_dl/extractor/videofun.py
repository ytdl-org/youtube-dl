from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import (
    compat_urllib_parse
)


class VideoFunIE(InfoExtractor):
    _VALID_URL = r'http://[w.]*videofun\.me/embed/(?P<id>[0-9a-f]+)'

    _TEST = {
        'url': 'http://videofun.me/embed/8267659be070860af600fee7deadbcdb?w=600&h=438',
        'md5': 'e37e99d665f503dd2db952f7c4dba9e6',
        'info_dict': {
            'id': 'Mahou-Shoujo-Madoka-Magica-07',
            'ext': 'flv',
            'title': 'Mahou-Shoujo-Madoka-Magica-07',
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(
            url, video_id, 'Downloading video page')

        video_url_encoded = self._html_search_regex(
            r'url: "(http://gateway\.videofun\.me[^"]+)"', webpage, 'video url')
        video_url = compat_urllib_parse.unquote(video_url_encoded)
        title = self._html_search_regex(r'.*/([^.]*)\.', video_url, 'title')

        return {
            'id': title,
            'url': video_url,
            'title': title,
        }
