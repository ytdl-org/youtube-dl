from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import get_element_by_id


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
        music_id = self._match_id(url)
        webpage = self._download_webpage(url, music_id)

        title = self._og_search_property('audio:title', webpage)
        description = re.sub(r'</?p>', '', get_element_by_id('sound_description',
            webpage).strip())

        return {
            'id': music_id,
            'title': title,
            'url': self._og_search_property('audio', webpage, 'music url'),
            'uploader': self._og_search_property('audio:artist', webpage,
                'music uploader', fatal=False),
            'description': description,
        }
