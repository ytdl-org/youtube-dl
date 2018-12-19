# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    int_or_none,
)


class TV8IE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?tv8\.com\.tr/[^/]+/(?P<id>[^?#&]+-video-?(?P<chapter>[0-9]+)?)\.htm'
    IE_NAME = 'tv8'
    _TESTS = [{
        'url': 'https://www.tv8.com.tr/yemekteyiz/yemekteyiz-281-bolum-13122018-52578-video.htm',
        'md5': '73be7e69708d37eb77643c12e8598b35',
        'info_dict': {
            'id': 'yemekteyiz-281-bolum-13122018-52578-video',
            'ext': 'mp4',
            'title': 'Yemekteyiz 281. bölüm (13/12/2018)',
            'description': 'md5:01a9cc2115550dfa3b51772239082f6a',
            'thumbnail': r're:^https?://.*\.jpg$',
            'duration': 8667,
            'timestamp': 1544780098,
            'upload_date': '20181214',
        },
    },
    {
        'url': 'https://www.tv8.com.tr/masterchef-turkiye/masterchef-turkiye-30-bolum-11122018-52440-video-3.htm',
        'only_matching': True
    }]

    def _real_extract(self, url):

        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')
        chapter_number = int_or_none(mobj.group('chapter')) or 1

        webpage = self._download_webpage(url, video_id)
        webpage = webpage.replace('URL', 'Url')

        info = {
            'id': video_id,
            'chapter_number': chapter_number,
        }

        json_ld = self._search_regex(
            r'(?is)<script[^>]+type=(["\'])application/ld\+json\1[^>]*>.*(?P<json_ld>{[^<]+VideoObject[^<]+}).*</script>', webpage, 'JSON-LD', group='json_ld')

        ld_info = self._json_ld(json_ld, video_id)
        info.update(ld_info)

        return info
