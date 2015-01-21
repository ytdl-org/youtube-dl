# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor


class StreetVoiceIE(InfoExtractor):
    _VALID_URL = r'http://tw.streetvoice.com/[^/]+/songs/(?P<id>[0-9]+)/'
    _TESTS = [
        {
            'url': 'http://tw.streetvoice.com/skippylu/songs/94440/',
            'md5': '15974627fc01a29e492c98593c2fd472',
            'info_dict': {
                'id': '94440',
                'ext': 'mp3',
                'title': '輸',
                'description': '輸 - Crispy脆樂團'
            }
        }
    ]

    def _real_extract(self, url):
        song_id = self._match_id(url)

        api_url = 'http://tw.streetvoice.com/music/api/song/%s/' % song_id
        info_dict = self._download_json(api_url, song_id)

        author = info_dict['musician']['name']
        title = info_dict['name']
        return {
            'id': song_id,
            'ext': 'mp3',
            'title': title,
            'url': info_dict['file'],
            'description': '%s - %s' % (title, author)
        }
