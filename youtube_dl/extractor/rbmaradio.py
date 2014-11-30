# encoding: utf-8
from __future__ import unicode_literals

import json
import re

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
)


class RBMARadioIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?rbmaradio\.com/shows/(?P<videoID>[^/]+)$'
    _TEST = {
        'url': 'http://www.rbmaradio.com/shows/ford-lopatin-live-at-primavera-sound-2011',
        'md5': '6bc6f9bcb18994b4c983bc3bf4384d95',
        'info_dict': {
            'id': 'ford-lopatin-live-at-primavera-sound-2011',
            'ext': 'mp3',
            "uploader_id": "ford-lopatin",
            "location": "Spain",
            "description": "Joel Ford and Daniel ’Oneohtrix Point Never’ Lopatin fly their midified pop extravaganza to Spain. Live at Primavera Sound 2011.",
            "uploader": "Ford & Lopatin",
            "title": "Live at Primavera Sound 2011",
        },
    }

    def _real_extract(self, url):
        m = re.match(self._VALID_URL, url)
        video_id = m.group('videoID')

        webpage = self._download_webpage(url, video_id)

        json_data = self._search_regex(r'window\.gon.*?gon\.show=(.+?);$',
                                       webpage, 'json data', flags=re.MULTILINE)

        try:
            data = json.loads(json_data)
        except ValueError as e:
            raise ExtractorError('Invalid JSON: ' + str(e))

        video_url = data['akamai_url'] + '&cbr=256'

        return {
            'id': video_id,
            'url': video_url,
            'title': data['title'],
            'description': data.get('teaser_text'),
            'location': data.get('country_of_origin'),
            'uploader': data.get('host', {}).get('name'),
            'uploader_id': data.get('host', {}).get('slug'),
            'thumbnail': data.get('image', {}).get('large_url_2x'),
            'duration': data.get('duration'),
        }
