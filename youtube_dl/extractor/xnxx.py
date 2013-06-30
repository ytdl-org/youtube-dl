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
    _TEST = {
        u'url': u'http://video.xnxx.com/video1135332/lida_naked_funny_actress_5_',
        u'file': u'1135332.flv',
        u'md5': u'0831677e2b4761795f68d417e0b7b445',
        u'info_dict': {
            u"title": u"lida \u00bb Naked Funny Actress  (5)"
        }
    }

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
