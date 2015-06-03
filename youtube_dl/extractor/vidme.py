from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import (
    int_or_none,
    float_or_none,
    str_to_int,
)


class VidmeIE(InfoExtractor):
    _VALID_URL = r'https?://vid\.me/(?:e/)?(?P<id>[\da-zA-Z]+)'
    _TESTS = [{
        'url': 'https://vid.me/QNB',
        'md5': 'f42d05e7149aeaec5c037b17e5d3dc82',
        'info_dict': {
            'id': 'QNB',
            'ext': 'mp4',
            'title': 'Fishing for piranha - the easy way',
            'description': 'source: https://www.facebook.com/photo.php?v=312276045600871',
            'duration': 119.92,
            'timestamp': 1406313244,
            'upload_date': '20140725',
            'thumbnail': 're:^https?://.*\.jpg',
        },
    }, {
        # From http://naked-yogi.tumblr.com/post/118312946248/naked-smoking-stretching
        'url': 'https://vid.me/e/Wmur',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        url = url.replace('vid.me/e/', 'vid.me/')
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        video_url = self._html_search_regex(
            r'<source src="([^"]+)"', webpage, 'video URL')

        title = self._og_search_title(webpage)
        description = self._og_search_description(webpage, default='')
        thumbnail = self._og_search_thumbnail(webpage)
        timestamp = int_or_none(self._og_search_property('updated_time', webpage, fatal=False))
        width = int_or_none(self._og_search_property('video:width', webpage, fatal=False))
        height = int_or_none(self._og_search_property('video:height', webpage, fatal=False))
        duration = float_or_none(self._html_search_regex(
            r'data-duration="([^"]+)"', webpage, 'duration', fatal=False))
        view_count = str_to_int(self._html_search_regex(
            r'<(?:li|span) class="video_views">\s*([\d,\.]+)\s*plays?', webpage, 'view count', fatal=False))
        like_count = str_to_int(self._html_search_regex(
            r'class="score js-video-vote-score"[^>]+data-score="([\d,\.\s]+)">',
            webpage, 'like count', fatal=False))

        return {
            'id': video_id,
            'url': video_url,
            'title': title,
            'description': description,
            'thumbnail': thumbnail,
            'timestamp': timestamp,
            'width': width,
            'height': height,
            'duration': duration,
            'view_count': view_count,
            'like_count': like_count,
        }
