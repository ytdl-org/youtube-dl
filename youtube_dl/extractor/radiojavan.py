from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    unified_strdate,
    str_to_int,
)


class RadioJavanIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?radiojavan\.com/videos/video/(?P<id>[^/]+)/?'
    _TEST = {
        'url': 'http://www.radiojavan.com/videos/video/chaartaar-ashoobam',
        'md5': 'e85208ffa3ca8b83534fca9fe19af95b',
        'info_dict': {
            'id': 'chaartaar-ashoobam',
            'ext': 'mp4',
            'title': 'Chaartaar - Ashoobam',
            'thumbnail': r're:^https?://.*\.jpe?g$',
            'upload_date': '20150215',
            'view_count': int,
            'like_count': int,
            'dislike_count': int,
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)

        webpage = self._download_webpage(url, video_id)

        formats = [{
            'url': 'https://media.rdjavan.com/media/music_video/%s' % video_path,
            'format_id': '%sp' % height,
            'height': int(height),
        } for height, video_path in re.findall(r"RJ\.video(\d+)p\s*=\s*'/?([^']+)'", webpage)]
        self._sort_formats(formats)

        title = self._og_search_title(webpage)
        thumbnail = self._og_search_thumbnail(webpage)

        upload_date = unified_strdate(self._search_regex(
            r'class="date_added">Date added: ([^<]+)<',
            webpage, 'upload date', fatal=False))

        view_count = str_to_int(self._search_regex(
            r'class="views">Plays: ([\d,]+)',
            webpage, 'view count', fatal=False))
        like_count = str_to_int(self._search_regex(
            r'class="rating">([\d,]+) likes',
            webpage, 'like count', fatal=False))
        dislike_count = str_to_int(self._search_regex(
            r'class="rating">([\d,]+) dislikes',
            webpage, 'dislike count', fatal=False))

        return {
            'id': video_id,
            'title': title,
            'thumbnail': thumbnail,
            'upload_date': upload_date,
            'view_count': view_count,
            'like_count': like_count,
            'dislike_count': dislike_count,
            'formats': formats,
        }
