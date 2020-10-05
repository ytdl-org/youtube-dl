# coding: utf-8
from __future__ import unicode_literals

import random
import re
import string
import time

from ctypes import c_int32

from .common import InfoExtractor
from ..compat import (
    compat_chr,
    compat_ord,
    compat_str,
    compat_urllib_parse_unquote,
    compat_urllib_parse_urlencode,
    compat_urlparse,
)
from ..utils import (
    ExtractorError,
    int_or_none,
    parse_duration,
    smuggle_url,
    std_headers,
    strip_jsonp,
    unescapeHTML,
    unsmuggle_url,
    url_or_none,
)


class WeTvBaseInfoExtractor(InfoExtractor):
    @staticmethod
    def parse_video_info(video_info):
        thumbnails = []
        for key, value in video_info.items():
            if key.startswith('pic_'):
                try:
                    width, height = key[4:].split('_')
                except ValueError:
                    pass
                else:
                    thumbnails.append({
                        'width': int_or_none(width),
                        'height': int_or_none(height),
                        'url': url_or_none(value),
                    })

        return {
            'id': video_info['vid'],
            'title': unescapeHTML(video_info['title']),
            'description': unescapeHTML(video_info.get('desc')),
            'duration': parse_duration(video_info.get('duration')),
            'episode_number': int_or_none(video_info.get('episode')),
            'thumbnails': thumbnails,
        }

    def extract_info_from_page(self, webpage, video_id):
        inputs = self._hidden_inputs(webpage)
        info = self._parse_json(inputs.get('data_sync', ''), video_id, compat_urllib_parse_unquote)

        return info, info['langInfo']['langId'], info['langInfo']['areaCode']


class WeTvIE(WeTvBaseInfoExtractor):
    IE_NAME = 'wetv'
    IE_DESC = 'WeTV.vip'
    _VALID_URL = r'''(?x)
        (?:
            wetv:|
            https?://(?:m\.)?wetv\.vip/
                (?:(?P<language>[a-z]{2}(?:-[a-z]{2})?)/)?
                (?:play/){,2}
                (?:(?P<playlist_id>[a-z\d]{15})(?:-[^/]*)?/)?
                (?:play\?vid=)?
        )
        (?P<id>[a-z\d]{11})
        (?:$|[^a-z\d])'''
    _TESTS = [
        {
            'url': 'https://wetv.vip/play?vid=o00318x0wds',
            'md5': 'e07ac4c842ed9363ee8a70ee3b72b047',
            'info_dict': {
                'id': 'o00318x0wds',
                'ext': 'mp4',
                'title': "EP1\uff1aThe King's Avatar",
                'thumbnail': r're:^https?://.*\.png.*$',
                'duration': 2696,
            },
            'params': {
                'hls_prefer_native': True,
            },
        },
        {
            'url': 'https://wetv.vip/en/play/jenizogwk2t8400/o00318x0wds',
            'only_matching': True,
        },
        {
            'url': "https://wetv.vip/en/play/jenizogwk2t8400-The%20King's%20Avatar/play?vid=o00318x0wds",
            'only_matching': True,
        },
        {
            'url': 'https://wetv.vip/en/play/a3150lwr4jn-Ve-Po-Ad%20Review%20%2F%20HowTo',
            'note': 'user video',
            'md5': '551b6d76d72a67933f25e6b7b078c865',
            'info_dict': {
                'id': 'a3150lwr4jn',
                'ext': 'mp4',
                'title': 'Ve-Po-Ad Review / HowTo',
            },
            'params': {
                'hls_prefer_native': True,
            },
        },
        {
            'url': 'https://wetv.vip/en/play/h31438yuulr',
            'note': 'non-m3u8',
            'md5': 'c1b83ac4653d38b2d5e423caeab4148b',
            'info_dict': {
                'id': 'h31438yuulr',
                'ext': 'mp4',
                'title': 'Gokukoku no Brynhildr - "Ichiban Boshi" \u2014 Full Ending',
            },
        },
    ]

    @staticmethod
    def create_guid():
        return ''.join([random.choice(string.digits + string.ascii_lowercase) for _ in range(32)])

    def _real_initialize(self):
        self.ckey = CKey()
        self.default_quality = 'hd'
        self.common_params = {
            'charge': 0,
            'defaultfmt': 'auto',
            'otype': 'json',
            'platform': 4830201,
            'sdtfrom': 1002,
            'defnpayver': 0,
            'appVer': '3.5.57',
            'sphttps': 1,
            'spwm': 4,
            'fhdswitch': 0,
            'show1080p': 0,
            'isHLS': 1,
            'dtype': 3,
            'sphls': 2,
            'spgzip': 1,
            'dlver': 2,
            'drm': 32,
            'spau': 1,
            'spaudio': 15,
            'spsrt': 1,
            'spvideo': 16,
            'defsrc': 2,
            'encryptVer': '8.1',
            'fp2p': 1,
            'spadseg': 1,
            'guid': WeTvIE.create_guid(),
            'logintoken': '{"main_login":"","openid":"","appid":"","access_token":"","vuserid":"","vusession":""}',
        }

    def generate_jsonp_url(self, quality, video_id, url, playlist_id, lang_code, country_code):
        parsed_url = compat_urlparse.urlparse(url)
        timestamp = time.time()

        params = self.common_params.copy()
        params.update({
            'defn': quality,
            'vid': video_id,
            'cid': playlist_id,
            'lang_code': lang_code,
            'country_code': country_code,
            'flowid': '{}_{}'.format(WeTvIE.create_guid(), params['platform']),
            'host': parsed_url.netloc,
            'refer': parsed_url.netloc,
            'ehost': compat_urlparse.urlunparse((parsed_url.scheme, parsed_url.netloc, parsed_url.path, None, None, None)),
            'tm': int(timestamp),
            '_{}'.format(int(timestamp * 1000)): '',
            'callback': 'txplayerJsonpCallBack_getinfo_{}'.format(random.randint(10000, 1000000)),
        })
        params['cKey'] = self.ckey.make(
            video_id, compat_str(params['tm']), params['appVer'], params['guid'],
            compat_str(params['platform']), url, std_headers['User-Agent'])

        return 'https://play.wetv.vip/getvinfo?{}'.format(compat_urllib_parse_urlencode(params))

    def get_jsonp_data(self, quality, video_id, *args):
        jsonp_url = self.generate_jsonp_url(quality, video_id, *args)
        # "accept-encoding: gzip" results in
        # EOFError: Compressed file ended before the end-of-stream marker was reached
        data = self._download_json(jsonp_url, video_id, transform_source=strip_jsonp,
                                   note='Downloading {} metadata'.format(quality),
                                   headers={'Accept-Encoding': 'deflate'})

        error_code = data.get('exem')
        if error_code == 0:
            return data
        elif error_code == -2:
            raise ExtractorError('This video is only available for VIP users.', expected=True)
        elif error_code == -12:
            raise ExtractorError('Bad encryption parameter')
        else:
            raise ExtractorError('Unknown error: [{}] {}'.format(error_code, data.get('msg')))

    @staticmethod
    def extract_qualities(data):
        qualities = []
        for quality in data['fl']['fi']:
            id = quality['name']
            qualities.append({
                'format_id': id,
                'format_note': quality['cname'],
                'filesize_approx': quality['fs'],
            })

        return qualities

    @staticmethod
    def extract_format(data):
        video_info = data['vl']['vi'][0]

        url = video_info['ul']['ui'][random.randint(0, 2)]['url']
        if 'fvkey' in video_info:
            url += '{}?vkey={}'.format(video_info['fn'], video_info['fvkey'])
        elif url.endswith('/'):
            url += '{}.m3u8?ver=4'.format(video_info['fn'])

        return {
            'url': url,
            'ext': 'mp4',
            'width': int_or_none(video_info.get('vw')),
            'height': int_or_none(video_info.get('vh')),
        }

    def get_formats_and_data(self, *args):
        formats = []

        default_quality_data = self.get_jsonp_data(self.default_quality, *args)
        qualities = WeTvIE.extract_qualities(default_quality_data)

        for quality in qualities:
            id = quality['format_id']
            if id == self.default_quality:
                data = default_quality_data
            else:
                data = self.get_jsonp_data(id, *args)

            quality.update(WeTvIE.extract_format(data))

            formats.append(quality)

        return formats, default_quality_data

    def _get_subtitles(self, data):
        subtitles = {}
        for subtitle_info in data['sfl'].get('fi', []):
            subtitles[subtitle_info['lang'].lower()] = [{'url': subtitle_info['url']}]

        return subtitles

    def _real_extract(self, url):
        url, smuggled_data = unsmuggle_url(url)

        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')
        language = mobj.group('language')
        # urls like this: https://wetv.vip/en/play/jenizogwk2t8400/play?vid=p0031yjo98d
        # when opened in new tab - load series page (and start playing the first episode)
        # when clicked on the website - load clicked episode
        # solution: use https://wetv.vip/en/play/p0031yjo98d instead
        good_url = 'https://wetv.vip/{}/play/{}'.format(language or 'en', video_id)

        if smuggled_data:
            # playlist extractor sets the metadata like title, duration, etc.,
            # no need to load the webpage again
            result = {}
            playlist_id = smuggled_data['playlist_id']
            lang_code = smuggled_data['lang_code']
            country_code = smuggled_data['country_code']
        else:
            webpage = self._download_webpage(good_url, video_id)

            full_url = self._og_search_url(webpage)
            mobj = re.match(self._VALID_URL, full_url)
            playlist_id = mobj.group('playlist_id') or ''

            info, lang_code, country_code = self.extract_info_from_page(webpage, video_id)
            result = WeTvBaseInfoExtractor.parse_video_info(info['videoInfo'])

        formats, data = self.get_formats_and_data(video_id, good_url, playlist_id, lang_code, country_code)

        subtitles = self.extract_subtitles(data)

        result.update({
            'id': video_id,
            'url': 'http://example.com/example.mp4',
            'formats': formats,
            'subtitles': subtitles,
        })
        return result


class WeTvPlaylistIE(WeTvBaseInfoExtractor):
    IE_NAME = 'wetv:playlist'
    IE_DESC = 'WeTV.vip playlists'
    _VALID_URL = r'''(?x)
        https?://(?:m\.)?wetv\.vip/
            (?:[a-z]{2}(?:-[a-z]{2})?/)?
            play(?:/|\?cid=)
            (?P<id>[a-z\d]{15})
            (?:-[^/]*)?
            (?:
                $|
                /(?!(?:play\?vid=)?[a-z\d]{11})
            )'''
    _TESTS = [
        {
            'url': 'https://wetv.vip/en/play/jenizogwk2t8400',
            'info_dict': {
                'id': 'jenizogwk2t8400',
                'title': "The King's Avatar",
                'description': 'md5:eca1c149133af485673d7676d4eff0c9',
            },
            'playlist_count': 40,
        },
        {
            'url': 'https://wetv.vip/play?cid=jenizogwk2t8400',
            'only_matching': True,
        },
        {
            'url': 'https://wetv.vip/en/play/0odpmck0od6ylsb',
            'note': 'movie',
            'info_dict': {
                'id': '0odpmck0od6ylsb',
                'title': 'Mystified',
                'description': 'md5:92717c44e1f89133c634cd5827c67636',
            },
            'playlist_count': 1,
        },
    ]

    def _real_extract(self, url):
        playlist_id = self._match_id(url)
        webpage = self._download_webpage(url, playlist_id)

        info, lang_code, country_code = self.extract_info_from_page(webpage, playlist_id)

        entries = []
        for video_info in info['videoList']:
            parsed_info = WeTvBaseInfoExtractor.parse_video_info(video_info)
            smuggled_url = smuggle_url(
                'wetv:{}'.format(parsed_info['id']),
                {
                    'playlist_id': playlist_id,
                    'lang_code': lang_code,
                    'country_code': country_code,
                })
            parsed_info.update({
                '_type': 'url_transparent',
                'url': smuggled_url,
                'ie_key': WeTvIE.ie_key(),
            })
            entries.append(parsed_info)

        return {
            '_type': 'playlist',
            'id': playlist_id,
            'title': info.get('coverInfo', {}).get('title'),
            'description': info.get('coverInfo', {}).get('description'),
            'entries': entries,
        }


class CKey(object):
    def __init__(self):
        self.encryption_arrays = [[
            1332468387, -1641050960, 2136896045, -1629555948,
            1399201960, -850809832, -1307058635, 751381793,
            -1933648423, 1106735553, -203378700, -550927659,
            766369351, 1817882502, -1615200142, 1083409063,
            -104955314, -1780208184, 173944250, 1254993693,
            1422337688, -1054667952, -880990486, -2119136777,
            -1822404972, 1380140484, -1723964626, 412019417,
            -890799303, -1734066435, 26893779, 420787978,
            -1337058067, 686432784, 695238595, 811911369,
            -391724567, -1068702727, -381903814, -648522509,
            -1266234148, 1959407397, -1644776673, 1152313324]]
        d = [None] * 256
        f = d[::]
        g = d[::]
        h = d[::]
        j = d[::]
        o = d[::]
        for i in range(256):
            o[i] = i << 1 if i < 128 else i << 1 ^ 283

        t = 0
        u = 0
        for i in range(256):
            v = u ^ u << 1 ^ u << 2 ^ u << 3 ^ u << 4
            v = CKey.rshift(v, 8) ^ 255 & v ^ 99
            d[t] = v
            x = o[t]
            z = o[o[x]]
            A = CKey.int32(257 * o[v] ^ 16843008 * v)
            f[t] = CKey.int32(A << 24 | CKey.rshift(A, 8))
            g[t] = CKey.int32(A << 16 | CKey.rshift(A, 16))
            h[t] = CKey.int32(A << 8 | CKey.rshift(A, 24))
            j[t] = A
            if t == 0:
                t = 1
                u = 1
            else:
                t = x ^ o[o[o[z ^ x]]]
                u ^= o[o[u]]

        self.encryption_arrays.append(f)
        self.encryption_arrays.append(g)
        self.encryption_arrays.append(h)
        self.encryption_arrays.append(j)
        self.encryption_arrays.append(d)

    @staticmethod
    def rshift(val, n):
        return (val & 0xFFFFFFFF) >> n

    @staticmethod
    def int32(val):
        return c_int32(val).value

    @staticmethod
    def encode_text(text):
        length = len(text)
        arr = [0] * (length // 4)
        for i in range(length):
            arr[i // 4] |= (255 & ord(text[i])) << 24 - i % 4 * 8
        return arr, length

    @staticmethod
    def decode_text(arr, length):
        text_array = []
        for i in range(length):
            text_array.append('{:02x}'.format(
                CKey.rshift(arr[i // 4], 24 - i % 4 * 8) & 255))

        return ''.join(text_array)

    @staticmethod
    def calculate_hash(text):
        result = 0
        for char in text:
            result = CKey.int32(result << 5) - result + compat_ord(char)
        return compat_str(result)

    @staticmethod
    def pad_text(text):
        pad_length = 16 - len(text) % 16
        return text + compat_chr(pad_length) * pad_length

    def encrypt(self, arr):
        for i in range(0, len(arr), 4):
            self.main_algorithm(arr, i)

    def main_algorithm(self, a, b):
        c, d, e, f, g, h = self.encryption_arrays

        if b == 0:
            xor_arr = [22039283, 1457920463, 776125350, -1941999367]
        else:
            xor_arr = a[b - 4: b]

        for i, val in enumerate(xor_arr):
            a[b + i] ^= val

        j = a[b] ^ c[0]
        k = a[b + 1] ^ c[1]
        l = a[b + 2] ^ c[2]
        m = a[b + 3] ^ c[3]
        n = 4
        for _ in range(9):
            q = (d[CKey.rshift(j, 24)] ^ e[CKey.rshift(k, 16) & 255]
                 ^ f[CKey.rshift(l, 8) & 255] ^ g[255 & m] ^ c[n])
            s = (d[CKey.rshift(k, 24)] ^ e[CKey.rshift(l, 16) & 255]
                 ^ f[CKey.rshift(m, 8) & 255] ^ g[255 & j] ^ c[n + 1])
            t = (d[CKey.rshift(l, 24)] ^ e[CKey.rshift(m, 16) & 255]
                 ^ f[CKey.rshift(j, 8) & 255] ^ g[255 & k] ^ c[n + 2])
            m = (d[CKey.rshift(m, 24)] ^ e[CKey.rshift(j, 16) & 255]
                 ^ f[CKey.rshift(k, 8) & 255] ^ g[255 & l] ^ c[n + 3])
            j = q
            k = s
            l = t
            n += 4

        q = CKey.int32(h[CKey.rshift(j, 24)] << 24
                       | h[CKey.rshift(k, 16) & 255] << 16
                       | h[CKey.rshift(l, 8) & 255] << 8
                       | h[255 & m]) ^ c[n]
        s = CKey.int32(h[CKey.rshift(k, 24)] << 24
                       | h[CKey.rshift(l, 16) & 255] << 16
                       | h[CKey.rshift(m, 8) & 255] << 8
                       | h[255 & j]) ^ c[n + 1]
        t = CKey.int32(h[CKey.rshift(l, 24)] << 24
                       | h[CKey.rshift(m, 16) & 255] << 16
                       | h[CKey.rshift(j, 8) & 255] << 8
                       | h[255 & k]) ^ c[n + 2]
        m = CKey.int32(h[CKey.rshift(m, 24)] << 24
                       | h[CKey.rshift(j, 16) & 255] << 16
                       | h[CKey.rshift(k, 8) & 255] << 8
                       | h[255 & l]) ^ c[n + 3]
        a[b] = q
        a[b + 1] = s
        a[b + 2] = t
        a[b + 3] = m

    def make(self, vid, tm, app_ver, guid, platform, url,
             # user_agent is shortened anyway
             user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:81.',
             referer='', nav_code_name='Mozilla',
             nav_name='Netscape', nav_platform='Win32'):
        text_parts = [
            '', vid, tm, 'mg3c3b04ba', app_ver, guid, platform,
            url[:48], user_agent[:48].lower(), referer[:48],
            nav_code_name, nav_name, nav_platform, '00', ''
        ]
        text_parts.insert(1, CKey.calculate_hash('|'.join(text_parts)))

        text = CKey.pad_text('|'.join(text_parts))
        [arr, length] = CKey.encode_text(text)
        self.encrypt(arr)
        return CKey.decode_text(arr, length).upper()
