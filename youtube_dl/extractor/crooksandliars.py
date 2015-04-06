from __future__ import unicode_literals

import json

from .common import InfoExtractor
from ..utils import (
    mimetype2ext,
)


class CrooksAndLiarsIE(InfoExtractor):
    _VALID_URL = r'(?:https?:)?//embed.crooksandliars.com/embed/(?P<id>[A-Za-z0-9]+)(?:$|[?#])'

    _TESTS = [{
        'url': 'https://embed.crooksandliars.com/embed/8RUoRhRi',
        'info_dict': {
            'id': 'https://embed.crooksandliars.com/embed/8RUoRhRi',
            'title': "Fox & Friends Says Protecting Atheists From Discrimination Is Anti-Christian!",
            'description': "Fox News, Fox & Friends Weekend, April 4, 2015. Read more... http://crooksandliars.com/2015/04/fox-friends-says-protecting-atheists",
            'timestamp': 1428207000,
            'thumbnail': 'https://crooksandliars.com/files/mediaposters/2015/04/31235.jpg?ts=1428207050',
            'uploader': "Heather",
        }
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        manifest = json.loads(self._html_search_regex(r'var manifest = ({.*?})\n', webpage, 'manifest JSON'))

        formats = []
        for item in manifest['flavors']:
            if not item['mime'].startswith('video/'): # XXX: or item['exclude']?
                continue
            formats.append({
                'format_id': item['type'],
                'ext': mimetype2ext(item['mime']),
                'url': item['url'],
            })

        # XXX: manifest['url']?
        return {
            'url': url,
            'id': video_id,
            'uploader': manifest['author'],
            'title': manifest['title'],
            'description': manifest['description'],
            'thumbnail': self._proto_relative_url(manifest['poster']),
            'duration': manifest['duration'],
            'timestamp': int(manifest['created']),
            'formats': formats,
        }

class CrooksAndLiarsArticleIE(InfoExtractor):
    _VALID_URL = r'(?:https?:)?//crooksandliars.com/\d+/\d+/(?P<id>[a-z\-]+)(?:/|$)'

    _TESTS = [{
        'url': 'http://crooksandliars.com/2015/04/fox-friends-says-protecting-atheists',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)
        player_url = self._proto_relative_url(self._html_search_regex(r'<iframe src="(//embed.crooksandliars.com/.*)"', webpage, 'embedded player'))

        return {
            '_type': 'url',
            'url': player_url
        }
