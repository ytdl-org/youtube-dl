import re

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
)

class HardSexTubeIE(InfoExtractor):
    _VALID_URL = r'^(?:http://)?(?:\w+\.)?hardsextube\.com/video/(?P<videoid>\d+)'
    _TEST = {
        u'url': u'http://www.hardsextube.com/video/939998/',
        u'file': u'939998.mp4',
        u'md5': u'9ffeca92da23e4b74e4116322496f44a',
        u'info_dict': {
            u"title": u"FUCKING MY REALDOLL AGAIN - ANAL AND VAGINAL",
            u"age_limit": 18,
        }
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)

        video_id = mobj.group('videoid')

        # Get webpage content
        murl = url.replace('www.', 'm.')
        webpage = self._download_webpage(murl, video_id)

        # Get the video title
        result = re.search(r'<img class="videoThumbs" src="([^"]+)"[^>]*title="([^"]+)"', webpage)
        if result is None:
            raise ExtractorError(u'ERROR: unable to extract title')

        video_thumb = result.group(1)
        video_title = result.group(2)

        # Get the video url
        video_url = self._html_search_regex(
            r'<div id="videoThumbs"[^>]*>\s+<a href="([^"]+)"', webpage, u'video url')

        info = {'id': video_id,
                'url': video_url,
                'title': video_title,
                'thumbnail': video_thumb,
                'ext': 'mp4',
                'age_limit': 18}

        return [info]
