# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import ExtractorError


class OrfiumTrackIE(InfoExtractor):
    _VALID_URL = r'https?://(www\.)?orfium\.com/track/(?P<id>\d+)'
    IE_NAME = 'orfium'
    _TEST = {
        'url': 'https://www.orfium.com/track/694466/misery-aciou/',
        'md5': 'ceae78f12a22b05d7f796e04de5f6cae',
        'info_dict': {
            'id': '694466',
            'title': 'misery',
            'artist': 'aciou',
            'thumbnail': 'https://g3w6qqdmbl.execute-api.us-west-1.amazonaws.com/prod/thumb/temp?url=https://s3-us-west-2.amazonaws.com/orfium-public/tracks/artwork/9f493b6e01d8416ca4b0417437b1709c.png&w=360&h=380',
            'url': 'https://cdn.orfium.com/tracks%2Fa281276f-8126-48aa-98ad-9121c282e6eb-1522252307.mp3',
            'ext': 'mp3'
        }
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        track_id = mobj.group('id')
        info_url = 'https://www.orfium.com/api/track/%s/info/' % track_id
        info_json = self._download_json(info_url, track_id, fatal=False)
        if info_json is None:
            raise ExtractorError('Track not found')
        track_file = info_json.get('file')

        return {
            'id': track_id,
            'title': info_json.get('title'),
            'artist': info_json.get('artist'),
            'thumbnail': info_json.get('image'),
            'url': track_file
        }
