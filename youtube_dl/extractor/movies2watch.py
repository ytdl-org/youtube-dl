# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor


# https://movies2watch.ru/movie/double-threat-wqyq6/1-full
class Movies2WatchIE(InfoExtractor):
    _VALID_URL = r'https?://movies2watch\.ru/movie/(?P<id>[^/?#&]+)/1-full'
    _TESTS = [{
        'url': 'https://movies2watch.ru/movie/double-threat-wqyq6/1-full',
        'md5': 'c4ce357bf745d4d27ef7f3b94c9a5dc9',
        'info_dict': {
            'id': 'double-threat-wqyq6',
            'ext': 'mp4',
            'title': 'Double Threat',
            'description': 'After skimming money from the mob, a beautiful young woman finds herself on the run with a kind stranger on a pilgrimage across the country to scatter his brother\'s ashes. In the heat of the moment, we quickly learn that her split personality comes in handy as the ruthless, dynamic side of her is unstoppable.'
        }
    }, {
        'url': 'https://movies2watch.ru/movie/the-batman-j2lx4/1-full',
        'md5': 'a6824ac8f96cdbf839a258493384ea5e',
        'info_dict': {
            'id': 'the-batman-j2lx4',
            'ext': 'mp4',
            'title': 'The Batman',
            'description': 'Two years of nights have turned Bruce Wayne into a nocturnal animal. But as he continues to find his way as Gotham\'s dark knight Bruce is forced into a game of cat and mouse with his biggest threat so far, a manic killer known as "The Riddler" who is filled with rage and determined to expose the corrupt system whilst picking off all of Gotham\'s key political figures. Working with both established and new allies, Bruce must track down the killer and see him brought to justice, while investigating his father\'s true legacy and questioning the affect that he has had on Gotham so far as "The Batman."'
        }
    }]

    def _real_extract(self, url):

        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        title = self._html_search_regex(r'<h1 itemprop="name" class="title">(.+?)</h1>', webpage, 'title')
        description = self._html_search_regex(r'<div itemprop="description" class="desc shorting" data-type="text">(.+?)</div>', webpage, 'description')

        return {
            'url': url,
            'id': video_id,
            'title': title,
            'description': description,
            'ext': 'mp4'
        }
