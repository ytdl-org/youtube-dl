# encoding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import int_or_none


class FirstTVIE(InfoExtractor):
    IE_NAME = 'firsttv'
    IE_DESC = 'Видеоархив - Первый канал'
    _VALID_URL = r'http://(?:www\.)?1tv\.ru/videoarchive/(?P<id>\d+)'

    _TEST = {
        'url': 'http://www.1tv.ru/videoarchive/73390',
        'md5': '3de6390cf0cca4a5eae1d1d83895e5ad',
        'info_dict': {
            'id': '73390',
            'ext': 'mp4',
            'title': 'Олимпийские канатные дороги',
            'description': 'md5:cc730d2bf4215463e37fff6a1e277b13',
            'thumbnail': 'http://img1.1tv.ru/imgsize640x360/PR20140210114657.JPG',
            'duration': 149,
        },
        'skip': 'Only works from Russia',
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')

        webpage = self._download_webpage(url, video_id, 'Downloading page')

        video_url = self._html_search_regex(
            r'''(?s)jwplayer\('flashvideoportal_1'\)\.setup\({.*?'file': '([^']+)'.*?}\);''', webpage, 'video URL')

        title = self._html_search_regex(
            r'<div class="tv_translation">\s*<h1><a href="[^"]+">([^<]*)</a>', webpage, 'title')
        description = self._html_search_regex(
            r'<div class="descr">\s*<div>&nbsp;</div>\s*<p>([^<]*)</p></div>', webpage, 'description', fatal=False)

        thumbnail = self._og_search_thumbnail(webpage)
        duration = self._og_search_property('video:duration', webpage, 'video duration', fatal=False)

        like_count = self._html_search_regex(r'title="Понравилось".*?/></label> \[(\d+)\]',
                                             webpage, 'like count', fatal=False)
        dislike_count = self._html_search_regex(r'title="Не понравилось".*?/></label> \[(\d+)\]',
                                                webpage, 'dislike count', fatal=False)

        return {
            'id': video_id,
            'url': video_url,
            'thumbnail': thumbnail,
            'title': title,
            'description': description,
            'duration': int_or_none(duration),
            'like_count': int_or_none(like_count),
            'dislike_count': int_or_none(dislike_count),
        }
