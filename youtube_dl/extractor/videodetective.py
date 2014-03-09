from __future__ import unicode_literals

import re

from .common import InfoExtractor
from .internetvideoarchive import InternetVideoArchiveIE
from ..utils import compat_urlparse


class VideoDetectiveIE(InfoExtractor):
    _VALID_URL = r'https?://www\.videodetective\.com/[^/]+/[^/]+/(?P<id>\d+)'

    _TEST = {
        'url': 'http://www.videodetective.com/movies/kick-ass-2/194487',
        'info_dict': {
            'id': '194487',
            'ext': 'mp4',
            'title': 'KICK-ASS 2',
            'description': 'md5:65ba37ad619165afac7d432eaded6013',
            'duration': 135,
        },
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')
        webpage = self._download_webpage(url, video_id)
        og_video = self._og_search_video_url(webpage)
        query = compat_urlparse.urlparse(og_video).query
        return self.url_result(InternetVideoArchiveIE._build_url(query), ie=InternetVideoArchiveIE.ie_key())
