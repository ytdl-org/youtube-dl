from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    compat_urllib_parse,
    determine_ext,
    ExtractorError,
)


class AUEngineIE(InfoExtractor):
    _TEST = {
        'url': 'http://auengine.com/embed.php?file=lfvlytY6&w=650&h=370',
        'file': 'lfvlytY6.mp4',
        'md5': '48972bdbcf1a3a2f5533e62425b41d4f',
        'info_dict': {
            'title': '[Commie]The Legend of the Legendary Heroes - 03 - Replication Eye (Alpha Stigma)[F9410F5A]'
        }
    }
    _VALID_URL = r'(?:http://)?(?:www\.)?auengine\.com/embed\.php\?.*?file=([^&]+).*?'

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group(1)
        webpage = self._download_webpage(url, video_id)
        title = self._html_search_regex(r'<title>(?P<title>.+?)</title>',
                webpage, 'title')
        title = title.strip()
        links = re.findall(r'\s(?:file|url):\s*["\']([^\'"]+)["\']', webpage)
        links = map(compat_urllib_parse.unquote, links)

        thumbnail = None
        video_url = None
        for link in links:
            if link.endswith('.png'):
                thumbnail = link
            elif '/videos/' in link:
                video_url = link
        if not video_url:
            raise ExtractorError(u'Could not find video URL')
        ext = '.' + determine_ext(video_url)
        if ext == title[-len(ext):]:
            title = title[:-len(ext)]

        return {
            'id':        video_id,
            'url':       video_url,
            'title':     title,
            'thumbnail': thumbnail,
        }
