import base64
import re

from .common import InfoExtractor
from ..utils import (
    compat_urllib_parse,

    ExtractorError,
)


class InfoQIE(InfoExtractor):
    _VALID_URL = r'^(?:https?://)?(?:www\.)?infoq\.com/[^/]+/[^/]+$'
    _TEST = {
        u"name": u"InfoQ",
        u"url": u"http://www.infoq.com/presentations/A-Few-of-My-Favorite-Python-Things",
        u"file": u"12-jan-pythonthings.mp4",
        u"info_dict": {
            u"description": u"Mike Pirnat presents some tips and tricks, standard libraries and third party packages that make programming in Python a richer experience.",
            u"title": u"A Few of My Favorite [Python] Things"
        },
        u"params": {
            u"skip_download": True
        }
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)

        webpage = self._download_webpage(url, video_id=url)
        self.report_extraction(url)

        # Extract video URL
        mobj = re.search(r"jsclassref ?= ?'([^']*)'", webpage)
        if mobj is None:
            raise ExtractorError(u'Unable to extract video url')
        real_id = compat_urllib_parse.unquote(base64.b64decode(mobj.group(1).encode('ascii')).decode('utf-8'))
        video_url = 'rtmpe://video.infoq.com/cfx/st/' + real_id

        # Extract title
        video_title = self._search_regex(r'contentTitle = "(.*?)";',
            webpage, u'title')

        # Extract description
        video_description = self._html_search_regex(r'<meta name="description" content="(.*)"(?:\s*/)?>',
            webpage, u'description', fatal=False)

        video_filename = video_url.split('/')[-1]
        video_id, extension = video_filename.split('.')

        info = {
            'id': video_id,
            'url': video_url,
            'uploader': None,
            'upload_date': None,
            'title': video_title,
            'ext': extension, # Extension is always(?) mp4, but seems to be flv
            'thumbnail': None,
            'description': video_description,
        }

        return [info]