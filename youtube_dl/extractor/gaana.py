# coding: utf-8
from __future__ import unicode_literals

import re
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
    bs = 32

    def _Decrypt(self, data):

        key = 'Z0AxbiEoZjEjci4wJCkmJQ=='
        iv = 'YXNkIUAjIUAjQCExMjMxMg=='

        stream_url = intlist_to_bytes(aes_cbc_decrypt(
            bytes_to_intlist(compat_b64decode(data)),
            bytes_to_intlist(compat_b64decode(key)),
            bytes_to_intlist(compat_b64decode(iv)))).decode()

        s = stream_url[:-ord(stream_url[len(stream_url) - 1:])]
        return s

    def _create_entry(self, data, video_id):

        raw_data = self._parse_json(data, video_id)

        video_data = raw_data.get('path')
        title = raw_data.get('title')
        thumbnail = raw_data.get('atw', '') or raw_data.get('albumartwork', '')
        duration = raw_data.get('duration')

        formats = []
        for value in video_data.keys():
            # need to skip auto
            if not value == 'auto':
                content = video_data.get(value)
                for k in content:
                    format_url = self._Decrypt(k.get('message'))
                    format_id = value

                    formats.append({
                        'url': format_url,
                        'format_id': format_id,
                        'ext': 'mp4'
                    })

        return {
            'id': video_id,
            'title': title,
            'description': raw_data.get('description'),
            'duration': int_or_none(duration),
            'formats': formats,
            'album': raw_data.get('albumtitle'),
            'thumbnail': thumbnail,
            'artist': raw_data.get('artist'),
            'release_date': raw_data.get('release_date'),
            'language': raw_data.get('language')
        }


class GaanaIE(GaanaBaseIE):
    IE_NAME = 'gaana'
    _VALID_URL = r'https?://(?:www\.)?gaana\.com/song/(?P<id>[^/#?]+)'
    _TESTS = [{
        # contentData
        'url': 'https://gaana.com/song/jeeye-to-jeeye-kaise',
        'info_dict': {
            'id': 'jeeye-to-jeeye-kaise',
            'ext': 'mp4',
            'title': 'Jeeye To Jeeye Kaise',
            'duration': 325,
        },
        'params': {
            # m3u8 download
            'skip_download': True,
        }
    }]
    _GEO_BYPASS = False

    def _real_extract(self, url):
        video_id = self._match_id(url)

        webpage = self._download_webpage(url, video_id)
        raw_data = self._search_regex(
            r'class="parentnode sourcelist_\d+"> (.*?) </span>',
            webpage, 'raw data')

        return self._create_entry(raw_data, video_id)


class GaanaAlbumIE(GaanaBaseIE):
    IE_NAME = 'gaana:album'
    _VALID_URL = r'https?://(?:www\.)?gaana\.com/album/(?P<id>[^/#?]+)'
    _TESTS = [{
        'url': 'https://gaana.com/album/saajan-hindi',
        'info_dict': {
            'id': 'saajan-hindi',
        },
        'playlist_mincount': 20,
    }, {
        'url': 'https://gaana.com/artist/kumar-sanu',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        playlist_id = self._match_id(url)
        webpage = self._download_webpage(url, playlist_id)
        matchobj = re.findall(r'class="parentnode sourcelist_\d+"> (.*?) </span>', webpage)
        entries = []
        for g in matchobj:
            entries.append(self._create_entry(g, playlist_id))

        return self.playlist_result(entries, playlist_id)
