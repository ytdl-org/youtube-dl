import re

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
)

class EmpflixIE(InfoExtractor):
    _VALID_URL = r'^https?://www\.empflix\.com/videos/(?P<videoid>[^\.]+)\.html'
    _TEST = {
        u'url': u'http://www.empflix.com/videos/Amateur-Finger-Fuck-33051.html',
        u'file': u'Amateur-Finger-Fuck-33051.flv',
        u'md5': u'5e5cc160f38ca9857f318eb97146e13e',
        u'info_dict': {
            u"title": u"Amateur Finger Fuck",
            u"age_limit": 18,
        }
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)

        video_id = mobj.group('videoid')

        # Get webpage content
        webpage = self._download_webpage(url, video_id)

        age_limit = self._rta_search(webpage)

        # Get the video title
        video_title = self._html_search_regex(r'name="title" value="(?P<title>[^"]*)"',
            webpage, u'title').strip()

        cfg_url = self._html_search_regex(r'flashvars\.config = escape\("([^"]+)"',
            webpage, u'flashvars.config').strip()

        cfg_xml = self._download_xml(cfg_url, video_id, note=u'Downloading metadata')
        video_url = cfg_xml.find('videoLink').text

        info = {'id': video_id,
                'url': video_url,
                'title': video_title,
                'ext': 'flv',
                'age_limit': age_limit}

        return [info]
