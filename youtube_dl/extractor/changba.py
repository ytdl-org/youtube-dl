# coding: utf-8
from __future__ import unicode_literals

import base64

from .common import InfoExtractor
from ..utils import (
    int_or_none,
    RegexNotFoundError,
)


class ChangbaIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?changba\.com/s/(?P<id>[0-9A-Za-z-_]+)'
    _TESTS = [{
        'url': 'https://changba.com/s/PBZkNLjjPmuE_nW7EuUNpg?&cbcode=Kxhsv6044ik&from=pcrecommend',
        'md5': '88aa70b832c4071cffd7e06d759bc7e8',
        'info_dict': {
            'id': '1146278955',
            'ext': 'mp4',
            'title': ' ',
            'vcodec': None
        }
    }, {
        'url': 'http://changba.com/s/nZqfbS_vCnieNNjJ7UiEGw?',
        'md5': 'e401463ffb03ed8900a0bccc641335e1',
        'info_dict': {
            'id': '1091968526',
            'ext': 'mp3',
            'title': '下雪 ',
            'vcodec': 'none'
        }
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)
        id = self._search_regex(r'workid=([0-9]+)', webpage, 'id')
        title = self._search_regex(
            r'<div[^>]+class="title"[^>]*>([^<]+)', webpage, 'title'
        )
        ext = None
        vcodec = None

        try:
            src_url = self._search_regex(r'var a="([^"]*)', webpage, 'url')
            ext = 'mp3'
            vcodec = 'none'
        except RegexNotFoundError:
            encoded = self._search_regex(
                r'video_url: \'([0-9A-Za-z]+=*)', webpage, 'video url'
            )
            src_url = base64.b64decode(encoded).decode('utf-8')
            ext = 'mp4'

        return {
            'url': src_url,
            'id': id,
            'ext': ext,
            'title': title,
            'vcodec': vcodec
        }
