import re

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
)


class LiveLeakIE(InfoExtractor):

    _VALID_URL = r'^(?:http?://)?(?:\w+\.)?liveleak\.com/view\?(?:.*?)i=(?P<video_id>[\w_]+)(?:.*)'
    IE_NAME = u'liveleak'

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        if mobj is None:
            raise ExtractorError(u'Invalid URL: %s' % url)

        video_id = mobj.group('video_id')

        webpage = self._download_webpage(url, video_id)

        video_url = self._search_regex(r'file: "(.*?)",',
            webpage, u'video URL')

        video_title = self._html_search_regex(r'<meta property="og:title" content="(?P<title>.*?)"',
            webpage, u'title').replace('LiveLeak.com -', '').strip()

        video_description = self._html_search_regex(r'<meta property="og:description" content="(?P<desc>.*?)"',
            webpage, u'description', fatal=False)

        video_uploader = self._html_search_regex(r'By:.*?(\w+)</a>',
            webpage, u'uploader', fatal=False)

        info = {
            'id':  video_id,
            'url': video_url,
            'ext': 'mp4',
            'title': video_title,
            'description': video_description,
            'uploader': video_uploader
        }

        return [info]
