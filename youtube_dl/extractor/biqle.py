# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor


class BIQLEIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?biqle\.(?:com|org|ru)/watch/(?P<id>-?\d+_\d+)'
    _TESTS = [{
        'url': 'http://www.biqle.ru/watch/847655_160197695',
        'md5': 'ad5f746a874ccded7b8f211aeea96637',
        'info_dict': {
            'id': '160197695',
            'ext': 'mp4',
            'title': 'Foo Fighters - The Pretender (Live at Wembley Stadium)',
            'uploader': 'Andrey Rogozin',
            'upload_date': '20110605',
        }
    }, {
        'url': 'https://biqle.org/watch/-44781847_168547604',
        'md5': '7f24e72af1db0edf7c1aaba513174f97',
        'info_dict': {
            'id': '168547604',
            'ext': 'mp4',
            'title': 'Ребенок в шоке от автоматической мойки',
            'uploader': 'Dmitry Kotov',
        },
        'skip': ' This video was marked as adult.  Embedding adult videos on external sites is prohibited.',
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)
        embed_url = self._proto_relative_url(self._search_regex(
            r'<iframe.+?src="((?:http:)?//daxab\.com/[^"]+)".*?></iframe>', webpage, 'embed url'))

        return {
            '_type': 'url_transparent',
            'url': embed_url,
        }
