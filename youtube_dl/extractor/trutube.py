import re

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
)


class TruTubeIE(InfoExtractor):
    _VALID_URL = r'(?:https?://)?(?:www\.)?(?P<url>trutube\.tv/video/(?P<videoid>.*/.*))'
    _TEST = {
        'url': ('http://www.trutube.tv/video/20814/Ernst-Zundel-met-les-Jui'
                'fs-en-guarde-VOSTFR'),
        'md5': '9973aa3c2870626799d2ac4e36cfc3dc',
        'info_dict': {
            u"title": u"TruTube.TV - Spitting in the face of die-versity",
            u"ext": u"mp4"
        }
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)

        video_id = mobj.group('videoid')

        # Get webpage content
        webpage = self._download_webpage(url, video_id)

        # Get the video title
        video_title = self._html_search_regex(r'<title>(?P<title>.*)</title>',
                                              webpage, 'title').strip()

        video_url = self._search_regex(r'(http://.*\.(?:mp4|flv))',
                                       webpage, u'video URL')

        ext = video_url[-3:]

        return {
            'id': video_id,
            'url': video_url,
            'title': video_title,
            'ext': ext
            }
