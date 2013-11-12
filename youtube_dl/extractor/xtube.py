import os
import re

from .common import InfoExtractor
from ..utils import (
    compat_urllib_parse_urlparse,
    compat_urllib_request,
    compat_urllib_parse,
)

class XTubeIE(InfoExtractor):
    _VALID_URL = r'^(?:https?://)?(?:www\.)?(?P<url>xtube\.com/watch\.php\?v=(?P<videoid>[^/?&]+))'
    _TEST = {
        u'url': u'http://www.xtube.com/watch.php?v=kVTUy_G222_',
        u'file': u'kVTUy_G222_.mp4',
        u'md5': u'092fbdd3cbe292c920ef6fc6a8a9cdab',
        u'info_dict': {
            u"title": u"strange erotica",
            u"description": u"surreal gay themed erotica...almost an ET kind of thing",
            u"uploader": u"greenshowers",
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

        video_title = self._html_search_regex(r'<div class="p_5px[^>]*>([^<]+)', webpage, u'title')
        video_uploader = self._html_search_regex(r'so_s\.addVariable\("owner_u", "([^"]+)', webpage, u'uploader', fatal=False)
        video_description = self._html_search_regex(r'<p class="video_description">([^<]+)', webpage, u'description', default=None)
        video_url= self._html_search_regex(r'var videoMp4 = "([^"]+)', webpage, u'video_url').replace('\\/', '/')
        path = compat_urllib_parse_urlparse(video_url).path
        extension = os.path.splitext(path)[1][1:]
        format = path.split('/')[5].split('_')[:2]
        format[0] += 'p'
        format[1] += 'k'
        format = "-".join(format)

        return {
            'id': video_id,
            'title': video_title,
            'uploader': video_uploader,
            'description': video_description,
            'url': video_url,
            'ext': extension,
            'format': format,
            'format_id': format,
            'age_limit': 18,
        }
