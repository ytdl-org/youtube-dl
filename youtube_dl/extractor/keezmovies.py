import os
import re

from .common import InfoExtractor
from ..utils import (
    compat_urllib_parse_urlparse,
    compat_urllib_request,
    compat_urllib_parse,
)
from ..aes import (
    aes_decrypt_text
)

class KeezMoviesIE(InfoExtractor):
    _VALID_URL = r'^(?:https?://)?(?:www\.)?(?P<url>keezmovies\.com/video/.+?(?P<videoid>[0-9]+))(?:[/?&]|$)'
    _TEST = {
        u'url': u'http://www.keezmovies.com/video/petite-asian-lady-mai-playing-in-bathtub-1214711',
        u'file': u'1214711.mp4',
        u'md5': u'6e297b7e789329923fcf83abb67c9289',
        u'info_dict': {
            u"title": u"Petite Asian Lady Mai Playing In Bathtub",
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

        # embedded video
        mobj = re.search(r'href="([^"]+)"></iframe>', webpage)
        if mobj:
            embedded_url = mobj.group(1)
            return self.url_result(embedded_url)

        video_title = self._html_search_regex(r'<h1 [^>]*>([^<]+)', webpage, u'title')
        video_url = compat_urllib_parse.unquote(self._html_search_regex(r'video_url=(.+?)&amp;', webpage, u'video_url'))
        if webpage.find('encrypted=true')!=-1:
            password = self._html_search_regex(r'video_title=(.+?)&amp;', webpage, u'password')
            video_url = aes_decrypt_text(video_url, password, 32).decode('utf-8')
        path = compat_urllib_parse_urlparse(video_url).path
        extension = os.path.splitext(path)[1][1:]
        format = path.split('/')[4].split('_')[:2]
        format = "-".join(format)

        age_limit = self._rta_search(webpage)

        return {
            'id': video_id,
            'title': video_title,
            'url': video_url,
            'ext': extension,
            'format': format,
            'format_id': format,
            'age_limit': age_limit,
        }
