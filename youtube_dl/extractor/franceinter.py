# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor


class FranceInterIE(InfoExtractor):
    _VALID_URL = r'http://(?:www\.)?franceinter\.fr/player/reecouter\?play=(?P<id>[0-9]{6})'
    _TEST = {
        'url': 'http://www.franceinter.fr/player/reecouter?play=793962',
        'file': '793962.mp3',
        'md5': '4764932e466e6f6c79c317d2e74f6884',
        "info_dict": {
            "title": "L’Histoire dans les jeux vidéo",
        },
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')

        webpage = self._download_webpage(url, video_id)
        title = self._html_search_regex(
            r'<span class="roll_overflow">(.*?)</span></h1>', webpage, 'title')
        path = self._search_regex(
            r'&urlAOD=(.*?)&startTime', webpage, 'video url')
        video_url = 'http://www.franceinter.fr/' + path

        return {
            'id': video_id,
            'formats': [{
                'url': video_url,
                'vcodec': 'none',
            }],
            'title': title,
        }
