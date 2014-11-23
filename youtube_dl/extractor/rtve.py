# encoding: utf-8
from __future__ import unicode_literals

import base64
import re
import time

from .common import InfoExtractor
from ..utils import (
    struct_unpack,
    remove_end,
)


def _decrypt_url(png):
    encrypted_data = base64.b64decode(png)
    text_index = encrypted_data.find(b'tEXt')
    text_chunk = encrypted_data[text_index - 4:]
    length = struct_unpack('!I', text_chunk[:4])[0]
    # Use bytearray to get integers when iterating in both python 2.x and 3.x
    data = bytearray(text_chunk[8:8 + length])
    data = [chr(b) for b in data if b != 0]
    hash_index = data.index('#')
    alphabet_data = data[:hash_index]
    url_data = data[hash_index + 1:]

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
            l = int(letter) * 10
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


class RTVEALaCartaIE(InfoExtractor):
    IE_NAME = 'rtve.es:alacarta'
    IE_DESC = 'RTVE a la carta'
    _VALID_URL = r'http://www\.rtve\.es/alacarta/videos/[^/]+/[^/]+/(?P<id>\d+)'

    _TESTS = [{
        'url': 'http://www.rtve.es/alacarta/videos/balonmano/o-swiss-cup-masculina-final-espana-suecia/2491869/',
        'md5': '1d49b7e1ca7a7502c56a4bf1b60f1b43',
        'info_dict': {
            'id': '2491869',
            'ext': 'mp4',
            'title': 'Balonmano - Swiss Cup masculina. Final: España-Suecia',
        },
    }, {
        'note': 'Live stream',
        'url': 'http://www.rtve.es/alacarta/videos/television/24h-live/1694255/',
        'info_dict': {
            'id': '1694255',
            'ext': 'flv',
            'title': 'TODO',
        }
    }]

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')
        info = self._download_json(
            'http://www.rtve.es/api/videos/%s/config/alacarta_videos.json' % video_id,
            video_id)['page']['items'][0]
        png_url = 'http://www.rtve.es/ztnr/movil/thumbnail/default/videos/%s.png' % video_id
        png = self._download_webpage(png_url, video_id, 'Downloading url information')
        video_url = _decrypt_url(png)

        return {
            'id': video_id,
            'title': info['title'],
            'url': video_url,
            'thumbnail': info.get('image'),
            'page_url': url,
        }


class RTVELiveIE(InfoExtractor):
    IE_NAME = 'rtve.es:live'
    IE_DESC = 'RTVE.es live streams'
    _VALID_URL = r'http://www\.rtve\.es/(?:deportes/directo|noticias|television)/(?P<id>[a-zA-Z0-9-]+)'

    _TESTS = [{
        'url': 'http://www.rtve.es/noticias/directo-la-1/',
        'info_dict': {
            'id': 'directo-la-1',
            'ext': 'flv',
            'title': 're:^La 1 de TVE [0-9]{4}-[0-9]{2}-[0-9]{2}Z[0-9]{6}$',
        },
        'params': {
            'skip_download': 'live stream',
        }
    }]

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        start_time = time.gmtime()
        video_id = mobj.group('id')

        webpage = self._download_webpage(url, video_id)
        player_url = self._search_regex(
            r'<param name="movie" value="([^"]+)"/>', webpage, 'player URL')
        title = remove_end(self._og_search_title(webpage), ' en directo')
        title += ' ' + time.strftime('%Y-%m-%dZ%H%M%S', start_time)

        vidplayer_id = self._search_regex(
            r' id="vidplayer([0-9]+)"', webpage, 'internal video ID')
        png_url = 'http://www.rtve.es/ztnr/movil/thumbnail/default/videos/%s.png' % vidplayer_id
        png = self._download_webpage(png_url, video_id, 'Downloading url information')
        video_url = _decrypt_url(png)

        return {
            'id': video_id,
            'ext': 'flv',
            'title': title,
            'url': video_url,
            'app': 'rtve-live-live?ovpfv=2.1.2',
            'player_url': player_url,
            'rtmp_live': True,
        }
