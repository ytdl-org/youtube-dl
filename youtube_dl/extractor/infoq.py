from __future__ import unicode_literals

import base64
import re

from .common import InfoExtractor
from ..utils import (
    compat_urllib_parse,
)


class InfoQIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?infoq\.com/[^/]+/(?P<id>[^/]+)$'

    _TEST = {
        'name': 'InfoQ',
        'url': 'http://www.infoq.com/presentations/A-Few-of-My-Favorite-Python-Things',
        'md5': 'fcaa3d995e04080dcb9465d86b5eef62',
        'info_dict': {
            'id': '12-jan-pythonthings',
            'ext': 'mp4',
            'description': 'Mike Pirnat presents some tips and tricks, standard libraries and third party packages that make programming in Python a richer experience.',
            'title': 'A Few of My Favorite [Python] Things',
        },
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')

        webpage = self._download_webpage(url, video_id)

        video_title = self._html_search_regex(r'<title>(.*?)</title>', webpage, 'title')
        video_description = self._html_search_meta('description', webpage, 'description')

        # The server URL is hardcoded
        video_url = 'rtmpe://video.infoq.com/cfx/st/'

        # Extract video URL
        encoded_id = self._search_regex(r"jsclassref ?= ?'([^']*)'", webpage, 'encoded id')
        real_id = compat_urllib_parse.unquote(base64.b64decode(encoded_id.encode('ascii')).decode('utf-8'))
        playpath = 'mp4:' + real_id

        video_filename = playpath.split('/')[-1]
        video_id, extension = video_filename.split('.')

        return {
            'id': video_id,
            'title': video_title,
            'description': video_description,
            'formats': [{
                'url': video_url,
                'ext': extension,
                'play_path': playpath,
            }],
        }
