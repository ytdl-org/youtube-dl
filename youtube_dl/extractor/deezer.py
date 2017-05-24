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
    h = md5hex(b"%d" % songid)
    key = b"g4el58wc0zvf9na1"
    return "".join(compat_chr(compat_ord(h[i]) ^ compat_ord(h[i + 16]) ^ compat_ord(key[i])) for i in range(16))


def getformat(song):
    """ return format id for a song """
    if song["FILESIZE_MP3_320"]:
        return 3
    if song["FILESIZE_MP3_256"]:
        return 5
    return 1


class DeezerPlaylistIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?deezer\.com/\w+/(?P<id>[0-9]+)'
    _TEST = {
        'url': 'http://www.deezer.com/playlist/176747451',
        'info_dict': {
            'id': '176747451',
            'title': 'Best!',
            'uploader': 'Anonymous',
            'thumbnail': r're:^https?://cdn-images.deezer.com/images/cover/.*\.jpg$',
        },
        'playlist_count': 30,
        'skip': 'Only available in .de',
    }

    def _real_extract(self, url):
        if 'test' not in self._downloader.params:
            self._downloader.report_warning('For now, this extractor only supports the 30 second previews. Patches welcome!')

        mobj = re.match(self._VALID_URL, url)
        playlist_id = mobj.group('id')

        webpage = self._download_webpage(url, playlist_id)
        geoblocking_msg = self._html_search_regex(
            r'<p class="soon-txt">(.*?)</p>', webpage, 'geoblocking message',
            default=None)
        if geoblocking_msg is not None:
            raise ExtractorError(
                'Deezer said: %s' % geoblocking_msg, expected=True)

        host_stream_cdn = self._search_regex(
            r'var HOST_STREAM_CDN = \'(.*?)\'', webpage, 'host stream cdn')

        data_json = self._search_regex(
            (r'__DZR_APP_STATE__\s*=\s*({.+?})\s*</script>',
             r'naboo\.display\(\'[^\']+\',\s*(.*?)\);\n'),
            webpage, 'data JSON')
        data = json.loads(data_json)

        playlist_title = data.get('DATA', {}).get('TITLE')
        playlist_uploader = data.get('DATA', {}).get('PARENT_USERNAME')
        # playlist_thumbnail = self._search_regex( r'<img id="naboo_playlist_image".*?src="([^"]+)"', webpage, 'playlist thumbnail')

        entries = []

        if 'SONGS' in data:
            # playlist, album
            songlist = data['SONGS']['data']
        elif 'MD5_ORIGIN' in data['DATA']:
            # track
            songlist = [data['DATA']]
        elif "ALBUMS" in data:
            songlist = []
            for album in data["ALBUMS"]["data"]:
                songlist.extend(album['SONGS']['data'])
        else:
            raise ExtractorError('Could not find songs')

        # album, playlist
        for s in songlist:

            urlkey = calcurlkey(int(s["SNG_ID"]), str(s["MD5_ORIGIN"]), int(s["MEDIA_VERSION"]), getformat(s))
            url = host_stream_cdn.replace('{0}', str(s["MD5_ORIGIN"])[0]) + "/" + urlkey

            formats = [{
                'format_id': 'preview',
                'key': calcblowfishkey(int(s["SNG_ID"])),
                'url': url,
                'preference': -100,  # Only the first 30 seconds
                'ext': 'mp3',
                'protocol': 'deezer',
            }]
            self._sort_formats(formats)
            artists = ', '.join(
                orderedSet(a['ART_NAME'] for a in s['ARTISTS']))
            entries.append({
                'id': s['SNG_ID'],
                'duration': int_or_none(s.get('DURATION')),
                'title': '%s - %s' % (artists, s['SNG_TITLE']),
                'uploader': s['ART_NAME'],
                'uploader_id': s['ART_ID'],
                'age_limit': 16 if s.get('EXPLICIT_LYRICS') == '1' else 0,
                'formats': formats,
            })

        return {
            '_type': 'playlist',
            'id': playlist_id,
            'title': playlist_title,
            'uploader': playlist_uploader,
            # 'thumbnail': playlist_thumbnail,
            'entries': entries,
        }
