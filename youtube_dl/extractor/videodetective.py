import re

from .common import InfoExtractor
from .internetvideoarchive import InternetVideoArchiveIE
from ..utils import (
    compat_urlparse,
)


class VideoDetectiveIE(InfoExtractor):
    _VALID_URL = r'https?://www\.videodetective\.com/[^/]+/[^/]+/(?P<id>\d+)'

    _TEST = {
        u'url': u'http://www.videodetective.com/movies/kick-ass-2/194487',
        u'file': u'194487.mp4',
        u'info_dict': {
            u'title': u'KICK-ASS 2',
            u'description': u'md5:65ba37ad619165afac7d432eaded6013',
            u'duration': 135,
        },
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')
        webpage = self._download_webpage(url, video_id)
        og_video = self._og_search_video_url(webpage)
        query = compat_urlparse.urlparse(og_video).query
        return self.url_result(InternetVideoArchiveIE._build_url(query),
            ie=InternetVideoArchiveIE.ie_key())
