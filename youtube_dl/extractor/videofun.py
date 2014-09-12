from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    compat_urllib_parse
)


class VideoFunIE(InfoExtractor):
    IE_NAME = 'videofun'
    IE_DESC = 'VideoFun'

    _VALID_URL = r'http://[w.]*videofun\.me/embed/(?P<id>.+)'

    _VIDEO_URL_REGEX = r'url: "(http://gateway\.videofun\.me[^"]+)"'
    _TITLE_REGEX = r'.*/(?P<title>[^.]*).'

    _TEST = {
        'url': 'http://videofun.me/embed/8267659be070860af600fee7deadbcdb?w=600&h=438',
        'md5': 'e37e99d665f503dd2db952f7c4dba9e6',
        'info_dict': {
            'id': 'Mahou-Shoujo-Madoka-Magica-07',
            'ext': 'flv',
            'title': 'Mahou-Shoujo-Madoka-Magica-07',
            'description': 'Mahou-Shoujo-Madoka-Magica-07'
        }
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')

        page = self._download_webpage(url, video_id, "Downloading video page")

        video_url_encoded = self._html_search_regex(self._VIDEO_URL_REGEX, page, 'url', fatal=True)
        video_url = compat_urllib_parse.unquote(video_url_encoded)

        title = re.match(self._TITLE_REGEX, video_url).group('title')

        return {
            'id': title,
            'url': video_url,
            'title': title,
            'description': title
        }
