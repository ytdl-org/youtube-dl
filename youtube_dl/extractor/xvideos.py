from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..compat import (
    compat_urllib_parse,
)
from ..utils import (
    clean_html,
    ExtractorError,
)


class XVideosIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?xvideos\.com/video(?P<id>[0-9]+)(?:.*)'
    _TEST = {
        'url': 'http://www.xvideos.com/video4588838/biker_takes_his_girl',
        'md5': '4b46ae6ea5e6e9086e714d883313c0c9',
        'info_dict': {
            'id': '4588838',
            'ext': 'flv',
            'title': 'Biker Takes his Girl',
            'age_limit': 18,
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        mobj = re.search(r'<h1 class="inlineError">(.+?)</h1>', webpage)
        if mobj:
            raise ExtractorError('%s said: %s' % (self.IE_NAME, clean_html(mobj.group(1))), expected=True)

        video_url = compat_urllib_parse.unquote(
            self._search_regex(r'flv_url=(.+?)&', webpage, 'video URL'))
        video_title = self._html_search_regex(
            r'<title>(.*?)\s+-\s+XVID', webpage, 'title')
        video_thumbnail = self._search_regex(
            r'url_bigthumb=(.+?)&amp', webpage, 'thumbnail', fatal=False)

        return {
            'id': video_id,
            'url': video_url,
            'title': video_title,
            'ext': 'flv',
            'thumbnail': video_thumbnail,
            'age_limit': 18,
        }
