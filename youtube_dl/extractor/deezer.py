from __future__ import unicode_literals

import json
import re

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    int_or_none,
    orderedSet,
    bytes_to_intlist,
    intlist_to_bytes,
)

from hashlib import md5
from ..aes import aes_ecb_encrypt

from binascii import b2a_hex
from ..compat import compat_ord, compat_chr


def md5hex(data):
    """ return hex string of md5 of the given string """
    return md5(data).hexdigest().encode('utf-8')


def calcurlkey(songid, md5origin, mediaver=4, fmt=1):
    """ Calculate the deezer download url given the songid, origin and media+format """
    data = b'\xa4'.join(_.encode("utf-8") for _ in [md5origin, str(fmt), str(songid), str(mediaver)])
    data = b'\xa4'.join([md5hex(data), data]) + b'\xa4'
    if len(data) % 16:
        data += b'\x00' * (16 - len(data) % 16)
    enc = aes_ecb_encrypt(bytes_to_intlist(data), bytes_to_intlist(b"jo6aey6haid2Teih"))
    return b2a_hex(intlist_to_bytes(enc)).decode('utf-8')


def calcblowfishkey(songid):
    """ Calculate the Blowfish decrypt key for a given songid """
    h = md5hex(str(songid).encode('ascii'))
    key = b"g4el58wc0zvf9na1"
    return "".join(compat_chr(compat_ord(h[i]) ^ compat_ord(h[i + 16]) ^ compat_ord(key[i])) for i in range(16))


def getformat(song):
    """ return format id for a song """
    if song["FILESIZE_MP3_320"]:
        return 3
    if song["FILESIZE_MP3_256"]:
        return 5
    return 1


class Format:
    def __init__(self, name, fmtid, ext, bitrate):
        self.name = name
        self.formatid = fmtid
        self.extension = ext
        self.bitrate = bitrate


_formatinfo = {
    'MP3_MISC': Format('MP3_MISC', 0, 'mp3', 128),
    'MP3_128': Format('MP3_128', 1, 'mp3', 128),
    # 2 used to be MP3_192
    'MP3_320': Format('MP3_320', 3, 'mp3', 320),
    # 4 used to be AAC_96
    'MP3_256': Format('MP3_256', 5, 'mp3', 256),
    'AAC_64': Format('AAC_64', 6, 'aac', 64),   # used to be AAC_192
    'MP3_192': Format('MP3_192', 7, 'mp3', 192),
    'AAC_96': Format('AAC_96', 8, 'aac', 96),
    'FLAC': Format('FLAC', 9, 'flac', 0),
    'MP3_64': Format('MP3_64', 10, 'mp3', 64),
    'MP3_32': Format('MP3_32', 11, 'mp3', 32),
}


def convert_to_int(x):
    try:
        return int(x)
    except:
        return 0


def songformats(s):
    """
    Enumerate all formats for a song
    """
    for k, v in s.items():
        if k.startswith("FILESIZE_") and convert_to_int(v):
            name = k[9:]
            if name in _formatinfo:
                yield _formatinfo[name]


class DeezerPlaylistIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?deezer\.com/(?P<type>\w+)/(?P<id>[0-9]+)'
    _TEST = {
        'url': 'http://www.deezer.com/playlist/176747451',
        'info_dict': {
            'id': '176747451',
            'title': 'Best!',
            'uploader': 'anonymous',
            'thumbnail': r're:^https?://\S*cdn-images.deezer.com/images/playlist/.*\.jpg$',
        },
        'playlist_count': 30,
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        list_id = mobj.group('id')
        list_type = mobj.group('type')

        webpage = self._download_webpage(url, list_id)
        geoblocking_msg = self._html_search_regex(
            r'<div class="page-soon.*<h2>(.*?)</h2>', webpage, 'geoblocking message',
            default=None)
        if geoblocking_msg is not None:
            raise ExtractorError(
                'Deezer said: %s' % geoblocking_msg, expected=True)

        host_stream_cdn = self._search_regex(
            r'var\s+HOST_STREAM_CDN\s*=\s*[\'"](.*?)[\'"]', webpage, 'host stream cdn')
        setting_domain_img = self._search_regex(
            r'var\s+SETTING_DOMAIN_IMG\s*=\s*[\'"](.*?)[\'"]', webpage, 'setting domain img')

        data_json = self._search_regex(
            (r'__DZR_APP_STATE__\s*=\s*({.+?})\s*</script>',
             r'naboo\.display\(\'[^\']+\',\s*(.*?)\);\n'),
            webpage, 'data JSON')
        data = json.loads(data_json)

        list_title = data.get('DATA', {}).get('TITLE')
        list_uploader = data.get('DATA', {}).get('PARENT_USERNAME')
        list_thumbnail = setting_domain_img + ("/playlist/" if list_type == 'playlist' else "/cover/")

        entries = []

        if 'SONGS' in data:
            # playlist, album
            songlist = data['SONGS']['data']
            if list_type == 'playlist':
                listimgid = data['DATA']['PLAYLIST_PICTURE']
            else:
                listimgid = data['DATA']['ALB_PICTURE']
        elif 'MD5_ORIGIN' in data['DATA']:
            # track
            songlist = [data['DATA']]
            listimgid = data['DATA']['ALB_PICTURE']
        elif "ALBUMS" in data:
            # artist
            songlist = []
            for album in data["ALBUMS"]["data"]:
                songlist.extend(album['SONGS']['data'])
            listimgid = data['DATA']['ART_PICTURE']
        else:
            raise ExtractorError('Could not find songs')

        for s in songlist:

            formats = []
            for fmt in songformats(s):
                urlkey = calcurlkey(int(s["SNG_ID"]), str(s["MD5_ORIGIN"]), int(s["MEDIA_VERSION"]), fmt.formatid)
                url = host_stream_cdn.replace('{0}', str(s["MD5_ORIGIN"])[0]) + "/" + urlkey

                formats.append({
                    'format_id': fmt.name,
                    'key': calcblowfishkey(int(s["SNG_ID"])),
                    'url': url,
                    'preference': fmt.bitrate,
                    'ext': fmt.extension,
                    'protocol': 'deezer',
                    'vcodec': 'none',
                })
            self._sort_formats(formats)
            artists = ', '.join(
                orderedSet(a['ART_NAME'] for a in s['ARTISTS']))
            entries.append({
                'id': s['SNG_ID'],
                'duration': int_or_none(s.get('DURATION')),
                'title': '%s - %s' % (artists, s['SNG_TITLE']),
                'artist': s['ART_NAME'],
                'track': s['SNG_TITLE'],
                'album': s['ALB_TITLE'],
                'track_number': s['TRACK_NUMBER'],
                'uploader': s['ART_NAME'],
                'uploader_id': s['ART_ID'],
                'age_limit': 16 if convert_to_int(s.get('EXPLICIT_LYRICS')) else 0,
                'formats': formats,
                'thumbnail': setting_domain_img + '/cover/' + s['ALB_PICTURE'] + '/200x200.jpg'
            })

        return {
            '_type': 'playlist',
            'id': list_id,
            'title': list_title,
            'uploader': list_uploader,
            'thumbnail': list_thumbnail + listimgid + '/200x200.jpg',
            'entries': entries,
        }
