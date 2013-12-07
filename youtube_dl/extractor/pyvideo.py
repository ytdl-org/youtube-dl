import re

from .common import InfoExtractor
from ..utils import determine_ext


class PyvideoIE(InfoExtractor):
    _VALID_URL = r'(?:http://)?(?:www\.)?break\.com/video/([^/]+)'
    _VALID_URL = r'(?:http://)?(?:www\.)?pyvideo\.org/video/(\d+)/(.*)'
    _TEST = {
        u'url': u'http://pyvideo.org/video/1737/become-a-logging-expert-in-30-minutes',
        u'file': u'Become a logging expert in 30 minutes-24_4WWkSmNo.mp4',
        u'md5': u'bf08cae24e1601027f98ae1262c299ad',
        u'info_dict': {
            u"title": u"Become a logging expert in 30 minutes"
        }
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group(2)
        webpage = self._download_webpage(url, video_id)
        m_youtube = re.search(r'(https?://www\.youtube\.com/watch\?v=.*)', webpage)

        if m_youtube is not None:
            return self.url_result(m_youtube.group(1), 'Youtube')
