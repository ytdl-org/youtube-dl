# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import (
    int_or_none,
    RegexNotFoundError,
)


class ChangbaIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?changba\.com/s/(?P<id>[0-9A-Za-z-_]+)'
    _TESTS = [{
        'url': 'https://changba.com/s/0GHVw6vyXv9N2FhaFi2WJg',
        'md5': 'ea55d17e939f3e2dabf483e47e8e5693',
        'info_dict': {
            'id': '1152860688',
            'ext': 'mp4',
            'title': '对你爱不完【炫酷慢摇】 ',
        }
    }, {
        'url': 'http://changba.com/s/nZqfbS_vCnieNNjJ7UiEGw?',
        'md5': 'e401463ffb03ed8900a0bccc641335e1',
        'info_dict': {
            'id': '1091968526',
            'ext': 'mp3',
            'title': '下雪 ',
        }
    }, {
        'url': 'http://changba.com/s/CPiNWbAa1qy0po0llqIJbg',
        'md5': '7adcc9afb85ace8ff854bdd0e8567f50',
        'info_dict': {
            'id': '136918054',
            'ext': 'mp3',
            'title': '红豆 ',
        }
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)
        id = self._search_regex(r'workid=([0-9]+)', webpage, 'id')
        title = self._search_regex(
            r'<div[^>]+class="title"[^>]*>([^<]+)', webpage, 'title'
        )
        # title = self._og_search_title(webpage)
        is_video = self._search_regex(r'&isvideo=([0-9])', webpage, 'isvideo')
        ext = 'mp3' if int_or_none(is_video) == 0 else 'mp4'

        try:
            src_url = self._search_regex(r'var a="([^"]*)', webpage, 'url')
        except RegexNotFoundError:
            src_url = 'http://lzscuw.changba.com/' + str(id) + '.' + ext

        return {
            'url': src_url,
            'id': id,
            'ext': ext,
            'title': title,
        }
