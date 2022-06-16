# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor


class QingTingIE(InfoExtractor):
    IE_NAME = 'QingTing'
    _VALID_URL = r'(?:https?://)?(?:www\.)?m\.(?:qingting\.fm|qtfm\.cn)/vchannels/\d+/programs/(?P<id>\d+)'
    _TEST = {
        'url': 'https://m.qingting.fm/vchannels/378005/programs/22257411/',
        'md5': '47e6a94f4e621ed832c316fd1888fb3c',
        'info_dict': {
            'id': '22257411',
            'ext': 'mp3',
            'title': '用了十年才修改，谁在乎教科书？-睡前消息-蜻蜓FM听头条',
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)
        title = self._html_search_regex(r'(?s)<title\b[^>]*>(.*)</title>', webpage, 'title', default=None) or self._og_search_title(webpage)
        url = self._search_regex(
            r'''("|')audioUrl\1\s*:\s*("|')(?P<url>(?:(?!\2).)*)\2''',
            webpage, 'audio URL')
        test_url = url_or_none(url)
        if not test_url:
            raise ExtractorError('Invalid audio URL %s' % (url, ))
        url = test_url
        return {
            'id': video_id,
            'title': title,
            'ext': 'mp3',
            'url': url,
        }
