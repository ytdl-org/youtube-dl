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
        "name": "InfoQ",
        "url": "http://www.infoq.com/presentations/A-Few-of-My-Favorite-Python-Things",
        "file": "12-jan-pythonthings.mp4",
        "info_dict": {
            "description": "Mike Pirnat presents some tips and tricks, standard libraries and third party packages that make programming in Python a richer experience.",
            "title": "A Few of My Favorite [Python] Things",
        },
        "params": {
            "skip_download": True,
        },
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')

        webpage = self._download_webpage(url, video_id)

        # Extract video URL
        encoded_id = self._search_regex(r"jsclassref ?= ?'([^']*)'", webpage, 'encoded id')
        real_id = compat_urllib_parse.unquote(base64.b64decode(encoded_id.encode('ascii')).decode('utf-8'))
        video_url = 'rtmpe://video.infoq.com/cfx/st/' + real_id

        # Extract title
        video_title = self._search_regex(r'contentTitle = "(.*?)";',
            webpage, 'title')

        # Extract description
        video_description = self._html_search_regex(r'<meta name="description" content="(.*)"(?:\s*/)?>',
            webpage, 'description', fatal=False)

        video_filename = video_url.split('/')[-1]
        video_id, extension = video_filename.split('.')

        return {
            'id': video_id,
            'url': video_url,
            'title': video_title,
            'ext': extension,  # Extension is always(?) mp4, but seems to be flv
            'description': video_description,
        }
