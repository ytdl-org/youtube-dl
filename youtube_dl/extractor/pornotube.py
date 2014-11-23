from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    compat_urllib_parse,

    unified_strdate,
)


class PornotubeIE(InfoExtractor):
    _VALID_URL = r'https?://(?:\w+\.)?pornotube\.com(/c/(?P<channel>[0-9]+))?(/m/(?P<videoid>[0-9]+))(/(?P<title>.+))$'
    _TEST = {
        'url': 'http://pornotube.com/c/173/m/1689755/Marilyn-Monroe-Bathing',
        'md5': '374dd6dcedd24234453b295209aa69b6',
        'info_dict': {
            'id': '1689755',
            'ext': 'flv',
            'upload_date': '20090708',
            'title': 'Marilyn-Monroe-Bathing',
            'age_limit': 18
        }
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)

        video_id = mobj.group('videoid')
        video_title = mobj.group('title')

        # Get webpage content
        webpage = self._download_webpage(url, video_id)

        # Get the video URL
        VIDEO_URL_RE = r'url: "(?P<url>http://video[0-9].pornotube.com/.+\.flv)",'
        video_url = self._search_regex(VIDEO_URL_RE, webpage, 'video url')
        video_url = compat_urllib_parse.unquote(video_url)

        # Get the uploaded date
        VIDEO_UPLOADED_RE = r'<div class="video_added_by">Added (?P<date>[0-9\/]+) by'
        upload_date = self._html_search_regex(VIDEO_UPLOADED_RE, webpage, 'upload date', fatal=False)
        if upload_date:
            upload_date = unified_strdate(upload_date)
        age_limit = self._rta_search(webpage)

        return {
            'id': video_id,
            'url': video_url,
            'upload_date': upload_date,
            'title': video_title,
            'ext': 'flv',
            'format': 'flv',
            'age_limit': age_limit,
        }
