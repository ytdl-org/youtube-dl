# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor


class ThisAmericanLifeIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?thisamericanlife\.org/radio-archives/episode/(?P<id>\d+)'
    _TEST = {
        'url': 'http://www.thisamericanlife.org/radio-archives/episode/487/harper-high-school-part-one',
        'md5': '5cda28076c9f9d1fd0b0f5cff5959948',
        'info_dict': {
            'id': '487',
            'title': '487: Harper High School, Part One',
            'url' : 'http://stream.thisamericanlife.org/487/stream/487_64k.m3u8',
            'ext': 'aac',
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        title = self._html_search_regex(r'<h1[^>]*>(.*?)</h1>', webpage, 'title')
        media_url = 'http://stream.thisamericanlife.org/' + video_id + '/stream/' + video_id + '_64k.m3u8'

        return {
            'id': video_id,
            'title': title,
            'url': media_url,
            'ext': 'aac',
        }
