from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    compat_urllib_parse
)


class Play44IE(InfoExtractor):
    IE_NAME = 'play44'
    IE_DESC = 'Play44'

    _VALID_URL = r'http://[w.]*play44\.net/embed\.php[^/]*/(?P<id>.+)'

    _VIDEO_URL_REGEX = r'_url = "(https?://[^"]+)";'
    _TITLE_REGEX = r'.*/(?P<title>[^.]*).'

    _TEST = {
        'url': 'http://play44.net/embed.php?w=600&h=438&vid=M/mahou-shoujo-madoka-magica-07.flv',
        'md5': 'e37e99d665f503dd2db952f7c4dba9e6',
        'info_dict': {
            'id': 'mahou-shoujo-madoka-magica-07',
            'ext': 'flv',
            'title': 'mahou-shoujo-madoka-magica-07',
            'description': 'mahou-shoujo-madoka-magica-07'
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

class ByZooIE(Play44IE):
    IE_NAME = "byzoo"
    IE_DESC = "ByZoo"

    _VALID_URL = r'http://[w.]*byzoo\.org/embed\.php[^/]*/(?P<id>.+)'

    _TEST = {
        'url': 'http://byzoo.org/embed.php?w=600&h=438&vid=at/nw/mahou_shoujo_madoka_magica_movie_3_-_part1.mp4',
        'md5': '455c83dabe2cd9fd74a87612b01fe017',
        'info_dict': {
            'id': 'mahou_shoujo_madoka_magica_movie_3_-_part1',
            'ext': 'mp4',
            'title': 'mahou_shoujo_madoka_magica_movie_3_-_part1',
            'description': 'mahou_shoujo_madoka_magica_movie_3_-_part1'
        }
    }

class Video44IE(Play44IE):
    IE_NAME = "video44"
    IE_DESC = "Video44"

    _VALID_URL = r'http://[w.]*video44\.net/.*file=(?P<id>[^&].).*'

    _TEST = {
        'url': 'http://www.video44.net/gogo/?w=600&h=438&file=chaoshead-12.flv&sv=1',
        'md5': '43eaec6d0beb10e8d42459b9f108aff3',
        'info_dict': {
            'id': 'chaoshead-12',
            'ext': 'mp4',
            'title': 'chaoshead-12',
            'description': 'chaoshead-12'
        }
    }
