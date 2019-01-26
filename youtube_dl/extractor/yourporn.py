from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import (urljoin, parse_duration)


class YourPornIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?yourporn\.sexy/post/(?P<id>[^/?#&.]+)'
    _TESTS = [{
        'url': 'https://yourporn.sexy/post/57ffcb2e1179b.html',
        'md5': '6f8682b6464033d87acaa7a8ff0c092e',
        'info_dict': {
            'id': '57ffcb2e1179b',
            'ext': 'mp4',
            'title': 'md5:c9f43630bd968267672651ba905a7d35',
            'thumbnail': r're:^https?://.*\.jpg$',
            'age_limit': 18
        },
    }, {
        'url': 'https://yourporn.sexy/post/5c2d2fde03bc5.html',
        'md5': '3b2323fb429d3f559a11b3f22f4754af',
        'info_dict': {
            'id': '5c2d2fde03bc5',
            'ext': 'mp4',
            'title': 'Busty 7 - Nubile Films (2018) - Chanel Preston, '
            'Crystal Swift, Jennifer Amton, Shay Evan',
            'thumbnail': r're:^https?://.*\.jpg$',
            'age_limit': 18,
            'duration': 5403
        }
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)

        webpage = self._download_webpage(url, video_id)

        video_url = urljoin(url, self._parse_json(
            self._search_regex(
                r'data-vnfo=(["\'])(?P<data>{.+?})\1', webpage, 'data info',
                group='data'),
            video_id)[video_id]).replace('/cdn/', '/cdn4/')

        title = (self._search_regex(
            r'<[^>]+\bclass=["\']PostEditTA[^>]+>([^<]+)', webpage, 'title',
            default=None) or self._og_search_description(webpage)).strip()

        thumbnail = self._og_search_thumbnail(webpage)

        duration = parse_duration(self._search_regex(r'Video Info -> duration:<b>([0-9:]+)</b>',
                                                     webpage, 'duration', default=None))
        return {
            'id': video_id,
            'url': video_url,
            'title': title,
            'duration': duration,
            'thumbnail': thumbnail,
            'age_limit': 18
        }
