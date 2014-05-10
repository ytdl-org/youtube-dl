import re

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
)

class SlutloadIE(InfoExtractor):
    _VALID_URL = r'^https?://(?:\w+\.)?slutload\.com/video/[^/]+/(?P<videoid>[^/]+)/?$'
    _TEST = {
        u'url': u'http://www.slutload.com/video/virginie-baisee-en-cam/TD73btpBqSxc/',
        u'file': u'TD73btpBqSxc.mp4',
        u'md5': u'0cf531ae8006b530bd9df947a6a0df77',
        u'info_dict': {
            u"title": u"virginie baisee en cam",
            u"age_limit": 18,
        }
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)

        video_id = mobj.group('videoid')

        # Get webpage content
        webpage = self._download_webpage(url, video_id)

        # Get the video title
        video_title = self._html_search_regex(r'<h1><strong>([^<]+)</strong>',
            webpage, u'title').strip()

        # Get the video url
        result = re.compile(r'<div id="vidPlayer"\s+data-url="([^"]+)"\s+previewer-file="([^"]+)"', re.S).search(webpage)
        if result is None:
            raise ExtractorError(u'ERROR: unable to extract video_url')

        video_url, video_thumb = result.group(1,2)

        info = {'id': video_id,
                'url': video_url,
                'title': video_title,
                'thumbnail': video_thumb,
                'ext': 'mp4',
                'age_limit': 18}

        return [info]
