from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import str_or_none


class ReverbNationIE(InfoExtractor):
    _VALID_URL = r'^https?://(?:www\.)?reverbnation\.com/.*?/song/(?P<id>\d+).*?$'
    _TESTS = [{
        'url': 'http://www.reverbnation.com/alkilados/song/16965047-mona-lisa',
        'md5': '3da12ebca28c67c111a7f8b262d3f7a7',
        'info_dict': {
            'id': '16965047',
            'ext': 'mp3',
            'title': 'MONA LISA',
            'uploader': 'ALKILADOS',
            'uploader_id': '216429',
            'thumbnail': 're:^https://gp1\.wac\.edgecastcdn\.net/.*?\.jpg$'
        },
    }]

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        song_id = mobj.group('id')

        api_res = self._download_json(
            'https://api.reverbnation.com/song/%s' % song_id,
            song_id,
            note='Downloading information of song %s' % song_id
        )

        return {
            'id': song_id,
            'title': api_res.get('name'),
            'url': api_res.get('url'),
            'uploader': api_res.get('artist', {}).get('name'),
            'uploader_id': str_or_none(api_res.get('artist', {}).get('id')),
            'thumbnail': self._proto_relative_url(
                api_res.get('image', api_res.get('thumbnail'))),
            'ext': 'mp3',
            'vcodec': 'none',
        }
