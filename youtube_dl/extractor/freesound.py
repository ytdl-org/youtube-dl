from __future__ import unicode_literals

import re

from .common import InfoExtractor


class FreesoundIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?freesound\.org/people/([^/]+)/sounds/(?P<id>[^/]+)'
    _TEST = {
        'url': 'http://www.freesound.org/people/miklovan/sounds/194503/',
        'md5': '12280ceb42c81f19a515c745eae07650',
        'info_dict': {
            'id': '194503',
            'ext': 'mp3',
            'title': 'gulls in the city.wav',
            'uploader': 'miklovan',
            'description': 'the sounds of seagulls in the city',
        }
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        music_id = mobj.group('id')
        webpage = self._download_webpage(url, music_id)
        title = self._html_search_regex(
            r'<div id="single_sample_header">.*?<a href="#">(.+?)</a>',
            webpage, 'music title', flags=re.DOTALL)
        description = self._html_search_regex(
            r'<div id="sound_description">(.*?)</div>', webpage, 'description',
            fatal=False, flags=re.DOTALL)

        return {
            'id': music_id,
            'title': title,
            'url': self._og_search_property('audio', webpage, 'music url'),
            'uploader': self._og_search_property('audio:artist', webpage, 'music uploader'),
            'description': description,
        }
