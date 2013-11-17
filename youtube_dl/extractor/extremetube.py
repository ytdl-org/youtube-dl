import os
import re

from .common import InfoExtractor
from ..utils import (
    compat_urllib_parse_urlparse,
    compat_urllib_request,
    compat_urllib_parse,
)

class ExtremeTubeIE(InfoExtractor):
    _VALID_URL = r'^(?:https?://)?(?:www\.)?(?P<url>extremetube\.com/video/.+?(?P<videoid>[0-9]+))(?:[/?&]|$)'
    _TEST = {
        u'url': u'http://www.extremetube.com/video/music-video-14-british-euro-brit-european-cumshots-swallow-652431',
        u'file': u'652431.mp4',
        u'md5': u'1fb9228f5e3332ec8c057d6ac36f33e0',
        u'info_dict': {
            u"title": u"Music Video 14 british euro brit european cumshots swallow",
            u"uploader": u"unknown",
            u"age_limit": 18,
        }
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('videoid')
        url = 'http://www.' + mobj.group('url')

        req = compat_urllib_request.Request(url)
        req.add_header('Cookie', 'age_verified=1')
        webpage = self._download_webpage(req, video_id)

        video_title = self._html_search_regex(r'<h1 [^>]*?title="([^"]+)"[^>]*>\1<', webpage, u'title')
        uploader = self._html_search_regex(r'>Posted by:(?=<)(?:\s|<[^>]*>)*(.+?)\|', webpage, u'uploader', fatal=False)
        video_url = compat_urllib_parse.unquote(self._html_search_regex(r'video_url=(.+?)&amp;', webpage, u'video_url'))
        path = compat_urllib_parse_urlparse(video_url).path
        extension = os.path.splitext(path)[1][1:]
        format = path.split('/')[5].split('_')[:2]
        format = "-".join(format)

        return {
            'id': video_id,
            'title': video_title,
            'uploader': uploader,
            'url': video_url,
            'ext': extension,
            'format': format,
            'format_id': format,
            'age_limit': 18,
        }
