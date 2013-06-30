import os.path
import re

from .common import InfoExtractor
from ..utils import (
    compat_urllib_parse,
    compat_urllib_parse_urlparse,
)

class AUEngineIE(InfoExtractor):
    _VALID_URL = r'(?:http://)?(?:www\.)?auengine\.com/embed.php\?.*?file=([^&]+).*?'

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group(1)
        webpage = self._download_webpage(url, video_id)
        title = self._html_search_regex(r'<title>(?P<title>.+?)</title>',
                webpage, u'title')
        title = title.strip()
        links = re.findall(r'[^A-Za-z0-9]?(?:file|url):\s*["\'](http[^\'"&]*)', webpage)
        links = [compat_urllib_parse.unquote(l) for l in links]
        for link in links:
            root, pathext = os.path.splitext(compat_urllib_parse_urlparse(link).path)
            if pathext == '.png':
                thumbnail = link
            elif pathext == '.mp4':
                url = link
                ext = pathext
        if ext == title[-len(ext):]:
            title = title[:-len(ext)]
        ext = ext[1:]
        return [{
            'id':        video_id,
            'url':       url,
            'ext':       ext,
            'title':     title,
            'thumbnail': thumbnail,
        }]
