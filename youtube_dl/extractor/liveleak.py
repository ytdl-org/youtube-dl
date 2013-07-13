import re

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
)


class LiveLeakIE(InfoExtractor):

    _VALID_URL = r'^(?:http?://)?(?:\w+\.)?liveleak\.com/view\?(?:.*?)i=(?P<video_id>[\w_]+)(?:.*)'
    IE_NAME = u'liveleak'
    _TEST = {
        u'url': u'http://www.liveleak.com/view?i=757_1364311680',
        u'file': u'757_1364311680.mp4',
        u'md5': u'0813c2430bea7a46bf13acf3406992f4',
        u'info_dict': {
            u"description": u"extremely bad day for this guy..!", 
            u"uploader": u"ljfriel2", 
            u"title": u"Most unlucky car accident"
        }
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        if mobj is None:
            raise ExtractorError(u'Invalid URL: %s' % url)

        video_id = mobj.group('video_id')

        webpage = self._download_webpage(url, video_id)

        video_url = self._search_regex(r'file: "(.*?)",',
            webpage, u'video URL')

        video_title = self._og_search_title(webpage).replace('LiveLeak.com -', '').strip()

        video_description = self._og_search_description(webpage)

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
