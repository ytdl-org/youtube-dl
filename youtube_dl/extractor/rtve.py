# encoding: utf-8
from __future__ import unicode_literals

import re
import base64

from .common import InfoExtractor
from ..utils import (
    struct_unpack,
)


class RTVEALaCartaIE(InfoExtractor):
    IE_NAME = 'rtve.es:alacarta'
    IE_DESC = 'RTVE a la carta'
    _VALID_URL = r'http://www\.rtve\.es/alacarta/videos/[^/]+/[^/]+/(?P<id>\d+)'

    _TEST = {
        'url': 'http://www.rtve.es/alacarta/videos/balonmano/o-swiss-cup-masculina-final-espana-suecia/2491869/',
        'md5': '18fcd45965bdd076efdb12cd7f6d7b9e',
        'info_dict': {
            'id': '2491869',
            'ext': 'mp4',
            'title': 'Balonmano - Swiss Cup masculina. Final: España-Suecia',
        },
    }

    def _decrypt_url(self, png):
        encrypted_data = base64.b64decode(png)
        text_index = encrypted_data.find(b'tEXt')
        text_chunk = encrypted_data[text_index-4:]
        length = struct_unpack('!I', text_chunk[:4])[0]
        # Use bytearray to get integers when iterating in both python 2.x and 3.x
        data = bytearray(text_chunk[8:8+length])
        data = [chr(b) for b in data if b != 0]
        hash_index = data.index('#')
        alphabet_data = data[:hash_index]
        url_data = data[hash_index+1:]

        alphabet = []
        e = 0
        d = 0
        for l in alphabet_data:
            if d == 0:
                alphabet.append(l)
                d = e = (e + 1) % 4
            else:
                d -= 1
        url = ''
        f = 0
        e = 3
        b = 1
        for letter in url_data:
            if f == 0:
                l = int(letter)*10
                f = 1
            else:
                if e == 0:
                    l += int(letter)
                    url += alphabet[l]
                    e = (b + 3) % 4
                    f = 0
                    b += 1
                else:
                    e -= 1

        return url

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')
        info = self._download_json(
            'http://www.rtve.es/api/videos/%s/config/alacarta_videos.json' % video_id,
            video_id)['page']['items'][0]
        png_url = 'http://www.rtve.es/ztnr/movil/thumbnail/default/videos/%s.png' % video_id
        png = self._download_webpage(png_url, video_id, 'Downloading url information')
        video_url = self._decrypt_url(png)

        return {
            'id': video_id,
            'title': info['title'],
            'url': video_url,
            'thumbnail': info['image'],
        }
