# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor


class OddshotIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?oddshot\.tv/shot/(?P<id>[0-9a-zA-Z\-]+)'
    _TEST = {
        'url': 'http://oddshot.tv/shot/esl-joindotared-2015090519512597',
        'md5': '86011224866356657ea12dc43f2281df',
        'info_dict': {
            'id': 'esl-joindotared-2015090519512597',
            'ext': 'mp4',
            'title': 'ESLOne NY EU qualifiers w/ @DotaCapitalist & @Blitz_Dota - Oddshot',
            'thumbnail': 'https://d301dinc95ec5f.cloudfront.net/thumbs/esl-joindotared-2015090519512597.shot.thumb.jpg'
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        title = self._html_search_regex(r'<title>(.*?)</title>', webpage, 'title')
        url = self._html_search_regex(r'<source src="(.*?)" ', webpage, 'url')

        return {
            'id': video_id,
            'title': title,
            'url': url,
            'thumbnail': self._og_search_thumbnail(webpage),
        }
