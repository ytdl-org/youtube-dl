from __future__ import unicode_literals

import re
import time

from .common import InfoExtractor
from ..utils import strip_jsonp


class ReverbNationIE(InfoExtractor):
    _VALID_URL = r'^https?://(?:www\.)?reverbnation\.com/.*?/song/(?P<id>\d+).*?$'
    _TESTS = [{
        'url': 'http://www.reverbnation.com/alkilados/song/16965047-mona-lisa',
        'file': '16965047.mp3',
        'md5': '3da12ebca28c67c111a7f8b262d3f7a7',
        'info_dict': {
            "title": "MONA LISA",
            "uploader": "ALKILADOS",
            "uploader_id": 216429,
            "thumbnail": "//gp1.wac.edgecastcdn.net/802892/production_public/Photo/13761700/image/1366002176_AVATAR_MONA_LISA.jpg"
        },
    }]

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        song_id = mobj.group('id')

        api_res = self._download_json(
            'https://api.reverbnation.com/song/%s?callback=api_response_5&_=%d'
                % (song_id, int(time.time() * 1000)),
            song_id,
            transform_source=strip_jsonp,
            note='Downloading information of song %s' % song_id
        )

        return {
            'id': song_id,
            'title': api_res.get('name'),
            'url': api_res.get('url'),
            'uploader': api_res.get('artist', {}).get('name'),
            'uploader_id': api_res.get('artist', {}).get('id'),
            'thumbnail': api_res.get('image', api_res.get('thumbnail')),
            'ext': 'mp3',
            'vcodec': 'none',
        }
