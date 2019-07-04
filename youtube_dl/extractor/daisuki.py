from __future__ import unicode_literals

import base64
import json
import random
import re

from .common import InfoExtractor
from ..aes import (
    aes_cbc_decrypt,
    aes_cbc_encrypt,
)
from ..compat import compat_b64decode
from ..utils import (
    bytes_to_intlist,
    bytes_to_long,
    extract_attributes,
    ExtractorError,
    intlist_to_bytes,
    js_to_json,
    int_or_none,
    long_to_bytes,
    pkcs1pad,
)


class DaisukiMottoIE(InfoExtractor):
    _VALID_URL = r'https?://motto\.daisuki\.net/framewatch/embed/[^/]+/(?P<id>[0-9a-zA-Z]{3})'

    _TEST = {
        'url': 'http://motto.daisuki.net/framewatch/embed/embedDRAGONBALLSUPERUniverseSurvivalsaga/V2e/760/428',
        'info_dict': {
            'id': 'V2e',
            'ext': 'mp4',
            'title': '#117 SHOWDOWN OF LOVE! ANDROIDS VS UNIVERSE 2!!',
            'subtitles': {
                'mul': [{
                    'ext': 'ttml',
                }],
            },
        },
        'params': {
            'skip_download': True,  # AES-encrypted HLS stream
        },
    }

    # The public key in PEM format can be found in clientlibs_anime_watch.min.js
    _RSA_KEY = (0xc5524c25e8e14b366b3754940beeb6f96cb7e2feef0b932c7659a0c5c3bf173d602464c2df73d693b513ae06ff1be8f367529ab30bf969c5640522181f2a0c51ea546ae120d3d8d908595e4eff765b389cde080a1ef7f1bbfb07411cc568db73b7f521cedf270cbfbe0ddbc29b1ac9d0f2d8f4359098caffee6d07915020077d, 65537)

    def _real_extract(self, url):
        video_id = self._match_id(url)

        webpage = self._download_webpage(url, video_id)

        flashvars = self._parse_json(self._search_regex(
            r'(?s)var\s+flashvars\s*=\s*({.+?});', webpage, 'flashvars'),
            video_id, transform_source=js_to_json)

        iv = [0] * 16

        data = {}
        for key in ('device_cd', 'mv_id', 'ss1_prm', 'ss2_prm', 'ss3_prm', 'ss_id'):
            data[key] = flashvars.get(key, '')

        encrypted_rtn = None

        # Some AES keys are rejected. Try it with different AES keys
        for idx in range(5):
            aes_key = [random.randint(0, 254) for _ in range(32)]
            padded_aeskey = intlist_to_bytes(pkcs1pad(aes_key, 128))

            n, e = self._RSA_KEY
            encrypted_aeskey = long_to_bytes(pow(bytes_to_long(padded_aeskey), e, n))
            init_data = self._download_json(
                'http://motto.daisuki.net/fastAPI/bgn/init/',
                video_id, query={
                    's': flashvars.get('s', ''),
                    'c': flashvars.get('ss3_prm', ''),
                    'e': url,
                    'd': base64.b64encode(intlist_to_bytes(aes_cbc_encrypt(
                        bytes_to_intlist(json.dumps(data)),
                        aes_key, iv))).decode('ascii'),
                    'a': base64.b64encode(encrypted_aeskey).decode('ascii'),
                }, note='Downloading JSON metadata' + (' (try #%d)' % (idx + 1) if idx > 0 else ''))

            if 'rtn' in init_data:
                encrypted_rtn = init_data['rtn']
                break

            self._sleep(5, video_id)

        if encrypted_rtn is None:
            raise ExtractorError('Failed to fetch init data')

        rtn = self._parse_json(
            intlist_to_bytes(aes_cbc_decrypt(bytes_to_intlist(
                compat_b64decode(encrypted_rtn)),
                aes_key, iv)).decode('utf-8').rstrip('\0'),
            video_id)

        title = rtn['title_str']

        formats = self._extract_m3u8_formats(
            rtn['play_url'], video_id, ext='mp4', entry_protocol='m3u8_native')

        subtitles = {}
        caption_url = rtn.get('caption_url')
        if caption_url:
            # mul: multiple languages
            subtitles['mul'] = [{
                'url': caption_url,
                'ext': 'ttml',
            }]

        return {
            'id': video_id,
            'title': title,
            'formats': formats,
            'subtitles': subtitles,
        }


class DaisukiMottoPlaylistIE(InfoExtractor):
    _VALID_URL = r'https?://motto\.daisuki\.net/(?P<id>information)/'

    _TEST = {
        'url': 'http://motto.daisuki.net/information/',
        'info_dict': {
            'title': 'DRAGON BALL SUPER',
        },
        'playlist_mincount': 117,
    }

    def _real_extract(self, url):
        playlist_id = self._match_id(url)

        webpage = self._download_webpage(url, playlist_id)

        entries = []
        for li in re.findall(r'(<li[^>]+?data-product_id="[a-zA-Z0-9]{3}"[^>]+>)', webpage):
            attr = extract_attributes(li)
            ad_id = attr.get('data-ad_id')
            product_id = attr.get('data-product_id')
            if ad_id and product_id:
                episode_id = attr.get('data-chapter')
                entries.append({
                    '_type': 'url_transparent',
                    'url': 'http://motto.daisuki.net/framewatch/embed/%s/%s/760/428' % (ad_id, product_id),
                    'episode_id': episode_id,
                    'episode_number': int_or_none(episode_id),
                    'ie_key': 'DaisukiMotto',
                })

        return self.playlist_result(entries, playlist_title='DRAGON BALL SUPER')
