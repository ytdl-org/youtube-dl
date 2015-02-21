from __future__ import unicode_literals

from .common import InfoExtractor
from ..compat import compat_urlparse
from .internetvideoarchive import InternetVideoArchiveIE


class VideoDetectiveIE(InfoExtractor):
    _VALID_URL = r'https?://www\.videodetective\.com/[^/]+/[^/]+/(?P<id>\d+)'

    _TEST = {
        'url': 'http://www.videodetective.com/movies/kick-ass-2/194487',
        'info_dict': {
            'id': '194487',
            'ext': 'mp4',
            'title': 'KICK-ASS 2',
            'description': 'md5:65ba37ad619165afac7d432eaded6013',
            'duration': 138,
        },
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)
        og_video = self._og_search_video_url(webpage)
        query = compat_urlparse.urlparse(og_video).query
        return self.url_result(InternetVideoArchiveIE._build_url(query), ie=InternetVideoArchiveIE.ie_key())
