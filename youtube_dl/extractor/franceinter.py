# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import int_or_none


class FranceInterIE(InfoExtractor):
    _VALID_URL = r'http://(?:www\.)?franceinter\.fr/player/reecouter\?play=(?P<id>[0-9]+)'
    _TEST = {
        'url': 'http://www.franceinter.fr/player/reecouter?play=793962',
        'md5': '4764932e466e6f6c79c317d2e74f6884',
        "info_dict": {
            'id': '793962',
            'ext': 'mp3',
            'title': 'L’Histoire dans les jeux vidéo',
            'description': 'md5:7e93ddb4451e7530022792240a3049c7',
            'timestamp': 1387369800,
            'upload_date': '20131218',
        },
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')

        webpage = self._download_webpage(url, video_id)

        path = self._search_regex(
            r'<a id="player".+?href="([^"]+)"', webpage, 'video url')
        video_url = 'http://www.franceinter.fr/' + path

        title = self._html_search_regex(
            r'<span class="title">(.+?)</span>', webpage, 'title')
        description = self._html_search_regex(
            r'<span class="description">(.*?)</span>',
            webpage, 'description', fatal=False)
        timestamp = int_or_none(self._search_regex(
            r'data-date="(\d+)"', webpage, 'upload date', fatal=False))

        return {
            'id': video_id,
            'title': title,
            'description': description,
            'timestamp': timestamp,
            'formats': [{
                'url': video_url,
                'vcodec': 'none',
            }],
        }
