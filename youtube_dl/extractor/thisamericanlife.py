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
            'thumbnail': 'http://www.thisamericanlife.org/sites/default/files/imagecache/large_square/episodes/487_lg_2.jpg',
            'description': 'We spent five months at Harper High School in Chicago, where last year alone 29 current and recent students were shot. 29. We went to get a sense of what it means to live in the midst of all this gun violence, how teens and adults navigate a world of funerals and Homecoming dances.',
        },
        'params': {
            # m38u download
            'skip_download': True,
        },
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        return {
            'id': video_id,
            'title': self._html_search_regex(r'<meta property="twitter:title" content="(.*?)"', webpage, 'title'),
            'url': 'http://stream.thisamericanlife.org/' + video_id + '/stream/' + video_id + '_64k.m3u8',
            'ext': 'aac',
            'thumbnail': self._html_search_regex(r'<meta property="og:image" content="(.*?)"', webpage, 'thumbnail'),
            'description': self._html_search_regex(r'<meta name="description" content="(.*?)"', webpage, 'description'),
        }
