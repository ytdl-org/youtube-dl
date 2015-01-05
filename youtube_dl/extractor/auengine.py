from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..compat import compat_urllib_parse
from ..utils import (
    determine_ext,
    ExtractorError,
    remove_end,
)


class AUEngineIE(InfoExtractor):
    _VALID_URL = r'http://(?:www\.)?auengine\.com/embed\.php\?.*?file=(?P<id>[^&]+).*?'

    _TEST = {
        'url': 'http://auengine.com/embed.php?file=lfvlytY6&w=650&h=370',
        'md5': '48972bdbcf1a3a2f5533e62425b41d4f',
        'info_dict': {
            'id': 'lfvlytY6',
            'ext': 'mp4',
            'title': '[Commie]The Legend of the Legendary Heroes - 03 - Replication Eye (Alpha Stigma)[F9410F5A]'
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)

        webpage = self._download_webpage(url, video_id)
        title = self._html_search_regex(
            r'<title>\s*(?P<title>.+?)\s*</title>', webpage, 'title')
        video_urls = re.findall(r'http://\w+.auengine.com/vod/.*[^\W]', webpage)
        video_url = compat_urllib_parse.unquote(video_urls[0])
        thumbnails = re.findall(r'http://\w+.auengine.com/thumb/.*[^\W]', webpage)
        thumbnail = compat_urllib_parse.unquote(thumbnails[0])

        if not video_url:
            raise ExtractorError('Could not find video URL')

        ext = '.' + determine_ext(video_url)
        title = remove_end(title, ext)

        return {
            'id': video_id,
            'url': video_url,
            'title': title,
            'thumbnail': thumbnail,
            'http_referer': 'http://www.auengine.com/flowplayer/flowplayer.commercial-3.2.14.swf',
        }
