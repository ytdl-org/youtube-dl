import re

from .common import InfoExtractor
from ..utils import (
    compat_urllib_parse,

    ExtractorError,
)


class XNXXIE(InfoExtractor):
    _VALID_URL = r'^(?:https?://)?video\.xnxx\.com/video([0-9]+)/(.*)'
    VIDEO_URL_RE = r'flv_url=(.*?)&amp;'
    VIDEO_TITLE_RE = r'<title>(.*?)\s+-\s+XNXX.COM'
    VIDEO_THUMB_RE = r'url_bigthumb=(.*?)&amp;'

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        if mobj is None:
            raise ExtractorError(u'Invalid URL: %s' % url)
        video_id = mobj.group(1)

        # Get webpage content
        webpage = self._download_webpage(url, video_id)

        video_url = self._search_regex(self.VIDEO_URL_RE,
            webpage, u'video URL')
        video_url = compat_urllib_parse.unquote(video_url)

        video_title = self._html_search_regex(self.VIDEO_TITLE_RE,
            webpage, u'title')

        video_thumbnail = self._search_regex(self.VIDEO_THUMB_RE,
            webpage, u'thumbnail', fatal=False)

        return [{
            'id': video_id,
            'url': video_url,
            'uploader': None,
            'upload_date': None,
            'title': video_title,
            'ext': 'flv',
            'thumbnail': video_thumbnail,
            'description': None,
        }]
