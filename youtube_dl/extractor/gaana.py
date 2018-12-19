# coding: utf-8
from __future__ import unicode_literals

import re
import hashlib
from ..aes import aes_cbc_decrypt
from ..compat import (
    compat_b64decode,
)

from .common import InfoExtractor
from ..utils import (
    bytes_to_intlist,
    intlist_to_bytes,
    int_or_none,
)


class GaanaBaseIE(InfoExtractor):
    _BASE_URL = 'https://gaana.com'
    _API_URL = 'https://apiv2.gaana.com/track/stream'
    _COOKIE = ''

    def _Decrypt(self, data):

        key = b'g@1n!(f1#r.0$)&%'
        iv = b'asd!@#!@#@!12312'
        stream_url = intlist_to_bytes(aes_cbc_decrypt(
            bytes_to_intlist(compat_b64decode(data)),
            bytes_to_intlist(key),
            bytes_to_intlist(iv))).decode()
        # unpad
        s = stream_url[:-ord(stream_url[len(stream_url) - 1:])]
        return s

    def _Create_ht(self, track_id):
        if not self._COOKIE:
            self._COOKIE = self._get_cookies(self._BASE_URL)['PHPSESSID'].value

        mess = track_id + '|' + self._COOKIE + '|03:40:31 sec'
        ht = hashlib.md5(mess.encode()).hexdigest() + self._COOKIE[3:9] + '='
        return ht

    def _create_entry(self, data, video_id):

        raw_data = self._parse_json(data, video_id)
        video_data = raw_data.get('path')
        title = raw_data.get('title')
        thumbnail = raw_data.get('albumartwork')
        duration = raw_data.get('duration')
        artist = raw_data.get('artist')

        def _format_artist(art):
            r_sample = r'#..(\d+)#..(\w+)[^|,]*'
            res = re.sub(r_sample, '', art)
            return re.sub(r',', ', ', res)

        artist = _format_artist(artist)

        formats = []
        if isinstance(video_data, dict):
            for value in video_data.keys():
                content = video_data.get(value)
                for k in content:
                    format_url = self._Decrypt(k.get('message'))

                    if value == 'auto':
                        format_id = 'normal'
                    else:
                        format_id = value

                    info = {
                        'url': format_url,
                        'format_id': format_id,
                        'ext': 'mp4',
                        'abr': int_or_none(k.get('bitRate')),
                        'format_note': 'mp4-aac'
                    }

                    if format_id == 'normal':
                        formats.insert(0, info)
                    else:
                        formats.append(info)

        else:
            track_id = raw_data.get('track_ids')
            ht = self._Create_ht(track_id)

            for g in ('normal', 'medium', 'high'):
                js = self._download_json(self._API_URL, title, headers={
                    'async': '1',
                    'method': 'POST'}, query={
                    'ht': ht,
                    'request_type': 'web',
                    'track_id': track_id,
                    'quality': g
                })
                format_url = js.get('stream_path')

                formats.append({
                    'url': format_url,
                    'format_id': g,
                    'ext': 'mp4',
                    'abr': int_or_none(js.get('bit_rate')),
                    'format_note': 'mp4-aac'
                })

        return {
            'id': video_id,
            'title': title,
            'duration': int_or_none(duration),
            'formats': formats,
            'album': raw_data.get('albumtitle'),
            'thumbnail': thumbnail,
            'artist': artist,
            'release_date': raw_data.get('release_date'),
            'language': raw_data.get('language')
        }


class GaanaIE(GaanaBaseIE):
    IE_NAME = 'gaana'
    _VALID_URL = r'https?://(?:www\.)?gaana\.com/(?P<idtype>(song|album|artist|playlist))/(?P<id>[^/#?]+)'
    _TESTS = [{
        'url': 'https://gaana.com/song/chamma-chamma-5',
        'md5': '11f926ce191e008fb82a3200ba047626',
        'info_dict': {
            'id': 'chamma-chamma-5',
            'ext': 'mp4',
            'title': 'Chamma Chamma',
            'thumbnail': r'https://a10.gaanacdn.com/images/song/86/24725286/crop_175x175_1544754220.jpg',
            'duration': '3:16',
            'album': 'Fraud Saiyaan',
            'artist': 'Neha Kakkar, Romi, Arun, Ikka',
            'language': 'Hindi',
            'release_date': 'Dec 14, 2018'
        }
    },
        {
        'url': 'https://gaana.com/album/simmba',
        'info_dict': [{
            'md5': '7f2ce83e8f6df7ed2cb50ce29d9f5d7f',
            'id': 'aankh-marey',
            'ext': 'mp4',
            'title': 'Aankh Marey',
            'thumbnail': r'https://a10.gaanacdn.com/images/song/88/24643688/crop_175x175_1544078542.jpg',
            'duration': '3:33',
            'album': 'Simmba',
            'artist': 'Neha Kakkar, Mika Singh, Kumar Sanu',
            'language': 'Hindi',
            'release_date': 'Dec 06, 2018'
        },
            {
            'md5': 'cdd78c5f3749ee0b114a26dfa454c64f',
            'id': 'tere-bin-111',
            'ext': 'mp4',
            'title': 'Tere Bin',
            'thumbnail': r'https://a10.gaanacdn.com/images/song/85/24725285/crop_175x175_1544753630.jpg',
            'duration': '3:51',
            'album': 'Simmba',
            'artist': 'Rahat Fateh Ali Khan, Asees Kaur, Tanishk Bagchi',
            'language': 'Hindi',
            'release_date': 'Dec 14, 2018'
        }]
    }]

    def _real_extract(self, url):
        r_match = re.match(self._VALID_URL, url)

        video_id = r_match.group('id')
        type_id = r_match.group('idtype')
        self.IE_NAME += ':' + type_id

        self._set_cookie(self._BASE_URL, 'PHPSESSID', 'val')
        webpage = self._download_webpage(url, video_id)

        matchobj = re.findall(r'class="parentnode sourcelist_\d+">(.*?)</span>', webpage)
        entries = []
        if len(matchobj) > 1:
            for g in matchobj:
                entries.append(self._create_entry(g, video_id))
            return self.playlist_result(entries, video_id)
        else:
            return self._create_entry(matchobj[0], video_id)
