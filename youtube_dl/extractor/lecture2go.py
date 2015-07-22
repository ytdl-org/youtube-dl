# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor


class Lecture2GoIE(InfoExtractor):
    _VALID_URL = r'https?://lecture2go.uni-hamburg.de/veranstaltungen/-/v/(?P<id>[0-9]+)'
    _TEST = {
        'url': 'https://lecture2go.uni-hamburg.de/veranstaltungen/-/v/17473',
        'md5': 'a9e76f83b3ef58019c4b7dbc35f406c1',
        'info_dict': {
            'id': '17473',
            'ext': 'mp4',
            'url': 'https://fms1.rrz.uni-hamburg.de/abo/64.050_FrankHeitmann_2015-04-13_14-35.mp4',
            'title': '2 - Endliche Automaten und reguläre Sprachen'
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        title = self._html_search_regex(r'<em class="title">(.*?)</em>', webpage, 'title')
        video_url = self._search_regex(r'b.isFirefox..a.useHTML5\).b.setOption.a,"src","(.*.mp4)"\).else', webpage, 'video_url')
        creator = self._html_search_regex(r'<div id="description">(.*)</div>', webpage, 'creator')

        return {
            'id': video_id,
            'title': title,
            'url': video_url,
            'creator': creator
        }
