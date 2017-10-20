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
from ..utils import (
    bytes_to_intlist,
    bytes_to_long,
    clean_html,
    ExtractorError,
    intlist_to_bytes,
    get_element_by_id,
    js_to_json,
    int_or_none,
    long_to_bytes,
    pkcs1pad,
    remove_end,
)


class DaisukiIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?daisuki\.net/[^/]+/[^/]+/[^/]+/watch\.[^.]+\.(?P<id>\d+)\.html'

    _TEST = {
        'url': 'http://www.daisuki.net/tw/en/anime/watch.TheIdolMasterCG.11213.html',
        'info_dict': {
            'id': '11213',
            'ext': 'mp4',
            'title': '#01 Who is in the pumpkin carriage? - THE IDOLM@STER CINDERELLA GIRLS',
            'subtitles': {
                'mul': [{
                    'ext': 'ttml',
                }],
            },
            'creator': 'BANDAI NAMCO Entertainment',
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
            init_data = self._download_json('http://www.daisuki.net/bin/bgn/init', video_id, query={
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
                base64.b64decode(encrypted_rtn)),
                aes_key, iv)).decode('utf-8').rstrip('\0'),
            video_id)

        formats = self._extract_m3u8_formats(
            rtn['play_url'], video_id, ext='mp4', entry_protocol='m3u8_native')

        title = remove_end(self._og_search_title(webpage), ' - DAISUKI')

        creator = self._html_search_regex(
            r'Creator\s*:\s*([^<]+)', webpage, 'creator', fatal=False)

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
            'creator': creator,
        }


class DaisukiPlaylistIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)daisuki\.net/[^/]+/[^/]+/[^/]+/detail\.(?P<id>[a-zA-Z0-9]+)\.html'

    _TEST = {
        'url': 'http://www.daisuki.net/tw/en/anime/detail.TheIdolMasterCG.html',
        'info_dict': {
            'id': 'TheIdolMasterCG',
            'title': 'THE IDOLM@STER CINDERELLA GIRLS',
            'description': 'md5:0f2c028a9339f7a2c7fbf839edc5c5d8',
        },
        'playlist_count': 26,
    }

    def _real_extract(self, url):
        playlist_id = self._match_id(url)

        webpage = self._download_webpage(url, playlist_id)

        episode_pattern = r'''(?sx)
            <img[^>]+delay="[^"]+/(\d+)/movie\.jpg".+?
            <p[^>]+class=".*?\bepisodeNumber\b.*?">(?:<a[^>]+>)?([^<]+)'''
        entries = [{
            '_type': 'url_transparent',
            'url': url.replace('detail', 'watch').replace('.html', '.' + movie_id + '.html'),
            'episode_id': episode_id,
            'episode_number': int_or_none(episode_id),
        } for movie_id, episode_id in re.findall(episode_pattern, webpage)]

        playlist_title = remove_end(
            self._og_search_title(webpage, fatal=False), ' - Anime - DAISUKI')
        playlist_description = clean_html(get_element_by_id('synopsisTxt', webpage))

        return self.playlist_result(entries, playlist_id, playlist_title, playlist_description)
