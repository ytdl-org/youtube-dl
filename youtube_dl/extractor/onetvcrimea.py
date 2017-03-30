# for issue #12466
# https://github.com/rg3/youtube-dl/issues/12466
# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from .common import InfoExtractor


class TvCrimeaIE(InfoExtractor):
    IE_NAME = '1tvcrimea'
    IE_DESC = '1 TV Crimea'
    _VALID_URL = r'https?://(?:www\.)?1tvcrimea.ru/(?P<id>.*)'
    _TESTS = {
        'url': 'http://1tvcrimea.ru/pages/category/000003-sportivnye/program/000031-moj-sport/video/025239-moj-sport',
        'md5': 'f79ca8774b6b276715038f26cfbb5c1b',
        'file': 'a',
        'info_dict': {
            'id': '2017-03-09-17-41-23-5769-moy-sport-efir-9-marta',
            'ext': 'mp4',
            # I had to encode this string because of my encoding and the fact that the title is in Cyrillic encoding
            'title': u'\u041C\u043E\u0439 \u0441\u043F\u043E\u0440\u0442 / \u0422\u0435\u043B\u0435\u0440\u0430\u0434\u0438\u043E\u043A\u043E\u043C\u043F\u0430\u043D\u0438\u044F "\u041A\u0440\u044B\u043C"',
        },
    }

    def _real_extract(self, url):
        # encode to UTF-8 because the webpage contains Cyrillic
        webpage = self._download_webpage(url, "")

        # url_pattern = re.compile('<a href="http://vid.techbee.pro:8080/vod/(.+?).mp4" target="_blank" rel="nofollow">', webpage, 'download')
        video_id = self._html_search_regex(r'<a href="http://vid.techbee.pro:8080/vod/(.+?).mp4" target="_blank" rel="nofollow">', webpage, 'url')
        video_url = "http://vid.techbee.pro:8080/vod/" + video_id + ".mp4"

        return {
            'id': video_id,
            'title': self._og_search_title(webpage),
            'url': video_url,
            'ext': 'mp4',
        }
