from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    parse_duration,
    parse_resolution,
    str_to_int,
)


class SpankBangIE(InfoExtractor):
    _VALID_URL = r'https?://(?:(?:www|m|[a-z]{2})\.)?spankbang\.com/(?P<id>[\da-z]+)/video'
    _TESTS = [{
        'url': 'http://spankbang.com/3vvn/video/fantasy+solo',
        'md5': '1cc433e1d6aa14bc376535b8679302f7',
        'info_dict': {
            'id': '3vvn',
            'ext': 'mp4',
            'title': 'fantasy solo',
            'description': 'dillion harper masturbates on a bed',
            'thumbnail': r're:^https?://.*\.jpg$',
            'uploader': 'silly2587',
            'age_limit': 18,
        }
    }, {
        # 480p only
        'url': 'http://spankbang.com/1vt0/video/solvane+gangbang',
        'only_matching': True,
    }, {
        # no uploader
        'url': 'http://spankbang.com/lklg/video/sex+with+anyone+wedding+edition+2',
        'only_matching': True,
    }, {
        # mobile page
        'url': 'http://m.spankbang.com/1o2de/video/can+t+remember+her+name',
        'only_matching': True,
    }, {
        # 4k
        'url': 'https://spankbang.com/1vwqx/video/jade+kush+solo+4k',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id, headers={
            'Cookie': 'country=US'
        })

        if re.search(r'<[^>]+\bid=["\']video_removed', webpage):
            raise ExtractorError(
                'Video %s is not available' % video_id, expected=True)

        formats = []
        for mobj in re.finditer(
                r'stream_url_(?P<id>[^\s=]+)\s*=\s*(["\'])(?P<url>(?:(?!\2).)+)\2',
                webpage):
            format_id, format_url = mobj.group('id', 'url')
            f = parse_resolution(format_id)
            f.update({
                'url': format_url,
                'format_id': format_id,
            })
            formats.append(f)
        self._sort_formats(formats)

        title = self._html_search_regex(
            r'(?s)<h1[^>]*>(.+?)</h1>', webpage, 'title')
        description = self._search_regex(
            r'<div[^>]+\bclass=["\']bottom[^>]+>\s*<p>[^<]*</p>\s*<p>([^<]+)',
            webpage, 'description', fatal=False)
        thumbnail = self._og_search_thumbnail(webpage)
        uploader = self._search_regex(
            r'class="user"[^>]*><img[^>]+>([^<]+)',
            webpage, 'uploader', default=None)
        duration = parse_duration(self._search_regex(
            r'<div[^>]+\bclass=["\']right_side[^>]+>\s*<span>([^<]+)',
            webpage, 'duration', fatal=False))
        view_count = str_to_int(self._search_regex(
            r'([\d,.]+)\s+plays', webpage, 'view count', fatal=False))

        age_limit = self._rta_search(webpage)

        return {
            'id': video_id,
            'title': title,
            'description': description,
            'thumbnail': thumbnail,
            'uploader': uploader,
            'duration': duration,
            'view_count': view_count,
            'formats': formats,
            'age_limit': age_limit,
        }
