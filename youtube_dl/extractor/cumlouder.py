from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import (
    parse_duration,
    str_to_int,
)

import re


class CumlouderIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?cumlouder\.com/porn-video/(?P<id>[^/]+)/?'
    _TEST = {
        'url': 'https://www.cumlouder.com/porn-video/jasmine-black-s-100-natural-tits/',
        'md5': 'cd893aaaace8c4ce7b33fc341c2f5fcf',
        'info_dict': {
            'id': 'jasmine-black-s-100-natural-tits',
            'ext': 'mp4',
            'title': 'Jasmine Black&#039;s 100% Natural Tits',
            'thumbnail': r're:^https?://.*\.jpg$',
            'age_limit': 18,
            'description': 'Cumlouder recommends Jasmine Black because, if you want to take care of yourself, '
                           'there&#039;s nothing better than a nice pair of 100-percent natural titties. Nick Moreno '
                           'is ready to enjoy the completely-free-of-artificial-additives boobs of Romanian star '
                           'Jasmine Black.',
            'duration': 607
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        title = self._search_regex(r'<h1><span[^>]+></span>(.+)</h1>', webpage, 'title').strip()

        thumbnail = self._search_regex(r'<video[^>]+poster=\'(https?://.+\.jpg)', webpage, 'thumbnail')

        video_url = "https:" + self._search_regex(r'<source[^>]+src=["\'](//[^("\')]+)', webpage, 'video_url')\
            .replace("&amp;", "&")

        description = self._search_regex(r'<strong>Description:</strong>([^<]+)', webpage, 'description').strip()

        view_count = str_to_int(self._search_regex(r'Views:\s+([\d]+)', webpage, 'view_count', default=None))

        tags = []
        for mobj in re.finditer(r'<a[^>]+class=(["\'])tag-link\1[^>]*title=\1(?P<tag>[^\'"]+)\1', webpage):
            tags.append(mobj.group('tag'))

        duration = parse_duration(self._search_regex(
            r'<span[^>]+class=["\'][^>]*ico-duracion[^>]+></span>\s*([0-9:]+)', webpage, 'duration',
            default=None))

        return {
            'id': video_id,
            'url': video_url,
            'title': title,
            'thumbnail': thumbnail,
            'age_limit': 18,
            'description': description,
            'view_count': view_count,
            'tags': tags,
            'duration': duration
        }
