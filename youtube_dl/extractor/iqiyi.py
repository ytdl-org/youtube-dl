# coding: utf-8
from __future__ import unicode_literals

import binascii
import hashlib
import itertools
import math
import re
import time

from .common import InfoExtractor
from ..compat import (
    compat_str,
    compat_urllib_parse_urlencode,
)
from ..utils import (
    decode_packed_codes,
    ExtractorError,
    intlist_to_bytes,
    ohdave_rsa_encrypt,
    remove_start,
    urshift,
)


def md5_text(text):
    return hashlib.md5(text.encode('utf-8')).hexdigest()


class IqiyiSDK(object):
    def __init__(self, target, ip, timestamp):
        self.target = target
        self.ip = ip
        self.timestamp = timestamp

    @staticmethod
    def split_sum(data):
        return compat_str(sum(map(lambda p: int(p, 16), list(data))))

    @staticmethod
    def digit_sum(num):
        if isinstance(num, int):
            num = compat_str(num)
        return compat_str(sum(map(int, num)))

    def even_odd(self):
        even = self.digit_sum(compat_str(self.timestamp)[::2])
        odd = self.digit_sum(compat_str(self.timestamp)[1::2])
        return even, odd

    def preprocess(self, chunksize):
        self.target = md5_text(self.target)
        chunks = []
        for i in range(32 // chunksize):
            chunks.append(self.target[chunksize * i:chunksize * (i + 1)])
        if 32 % chunksize:
            chunks.append(self.target[32 - 32 % chunksize:])
        return chunks, list(map(int, self.ip.split('.')))

    def mod(self, modulus):
        chunks, ip = self.preprocess(32)
        self.target = chunks[0] + ''.join(map(lambda p: compat_str(p % modulus), ip))

    def split(self, chunksize):
        modulus_map = {
            4: 256,
            5: 10,
            8: 100,
        }

        chunks, ip = self.preprocess(chunksize)
        ret = ''
        for i in range(len(chunks)):
            ip_part = compat_str(ip[i] % modulus_map[chunksize]) if i < 4 else ''
            if chunksize == 8:
                ret += ip_part + chunks[i]
            else:
                ret += chunks[i] + ip_part
        self.target = ret

    def handle_input16(self):
        self.target = md5_text(self.target)
        self.target = self.split_sum(self.target[:16]) + self.target + self.split_sum(self.target[16:])

    def handle_input8(self):
        self.target = md5_text(self.target)
        ret = ''
        for i in range(4):
            part = self.target[8 * i:8 * (i + 1)]
            ret += self.split_sum(part) + part
        self.target = ret

    def handleSum(self):
        self.target = md5_text(self.target)
        self.target = self.split_sum(self.target) + self.target

    def date(self, scheme):
        self.target = md5_text(self.target)
        d = time.localtime(self.timestamp)
        strings = {
            'y': compat_str(d.tm_year),
            'm': '%02d' % d.tm_mon,
            'd': '%02d' % d.tm_mday,
        }
        self.target += ''.join(map(lambda c: strings[c], list(scheme)))

    def split_time_even_odd(self):
        even, odd = self.even_odd()
        self.target = odd + md5_text(self.target) + even

    def split_time_odd_even(self):
        even, odd = self.even_odd()
        self.target = even + md5_text(self.target) + odd

    def split_ip_time_sum(self):
        chunks, ip = self.preprocess(32)
        self.target = compat_str(sum(ip)) + chunks[0] + self.digit_sum(self.timestamp)

    def split_time_ip_sum(self):
        chunks, ip = self.preprocess(32)
        self.target = self.digit_sum(self.timestamp) + chunks[0] + compat_str(sum(ip))


class IqiyiSDKInterpreter(object):
    def __init__(self, sdk_code):
        self.sdk_code = sdk_code

    def run(self, target, ip, timestamp):
        self.sdk_code = decode_packed_codes(self.sdk_code)

        functions = re.findall(r'input=([a-zA-Z0-9]+)\(input', self.sdk_code)

        sdk = IqiyiSDK(target, ip, timestamp)

        other_functions = {
            'handleSum': sdk.handleSum,
            'handleInput8': sdk.handle_input8,
            'handleInput16': sdk.handle_input16,
            'splitTimeEvenOdd': sdk.split_time_even_odd,
            'splitTimeOddEven': sdk.split_time_odd_even,
            'splitIpTimeSum': sdk.split_ip_time_sum,
            'splitTimeIpSum': sdk.split_time_ip_sum,
        }
        for function in functions:
            if re.match(r'mod\d+', function):
                sdk.mod(int(function[3:]))
            elif re.match(r'date[ymd]{3}', function):
                sdk.date(function[4:])
            elif re.match(r'split\d+', function):
                sdk.split(int(function[5:]))
            elif function in other_functions:
                other_functions[function]()
            else:
                raise ExtractorError('Unknown funcion %s' % function)

        return sdk.target


class IqiyiIE(InfoExtractor):
    IE_NAME = 'iqiyi'
    IE_DESC = '爱奇艺'

    _VALID_URL = r'https?://(?:(?:[^.]+\.)?iqiyi\.com|www\.pps\.tv)/.+\.html'

    _NETRC_MACHINE = 'iqiyi'

    _TESTS = [{
        'url': 'http://www.iqiyi.com/v_19rrojlavg.html',
        'md5': '470a6c160618577166db1a7aac5a3606',
        'info_dict': {
            'id': '9c1fb1b99d192b21c559e5a1a2cb3c73',
            'ext': 'mp4',
            'title': '美国德州空中惊现奇异云团 酷似UFO',
        }
    }, {
        'url': 'http://www.iqiyi.com/v_19rrhnnclk.html',
        'md5': 'f09f0a6a59b2da66a26bf4eda669a4cc',
        'info_dict': {
            'id': 'e3f585b550a280af23c98b6cb2be19fb',
            'ext': 'mp4',
            'title': '名侦探柯南 国语版',
        },
        'skip': 'Geo-restricted to China',
    }, {
        'url': 'http://www.iqiyi.com/w_19rt6o8t9p.html',
        'only_matching': True,
    }, {
        'url': 'http://www.iqiyi.com/a_19rrhbc6kt.html',
        'only_matching': True,
    }, {
        'url': 'http://yule.iqiyi.com/pcb.html',
        'only_matching': True,
    }, {
        # VIP-only video. The first 2 parts (6 minutes) are available without login
        # MD5 sums omitted as values are different on Travis CI and my machine
        'url': 'http://www.iqiyi.com/v_19rrny4w8w.html',
        'info_dict': {
            'id': 'f3cf468b39dddb30d676f89a91200dc1',
            'title': '泰坦尼克号',
        },
        'playlist': [{
            'info_dict': {
                'id': 'f3cf468b39dddb30d676f89a91200dc1_part1',
                'ext': 'f4v',
                'title': '泰坦尼克号',
            },
        }, {
            'info_dict': {
                'id': 'f3cf468b39dddb30d676f89a91200dc1_part2',
                'ext': 'f4v',
                'title': '泰坦尼克号',
            },
        }],
        'expected_warnings': ['Needs a VIP account for full video'],
    }, {
        'url': 'http://www.iqiyi.com/a_19rrhb8ce1.html',
        'info_dict': {
            'id': '202918101',
            'title': '灌篮高手 国语版',
        },
        'playlist_count': 101,
    }, {
        'url': 'http://www.pps.tv/w_19rrbav0ph.html',
        'only_matching': True,
    }]

    _FORMATS_MAP = [
        ('1', 'h6'),
        ('2', 'h5'),
        ('3', 'h4'),
        ('4', 'h3'),
        ('5', 'h2'),
        ('10', 'h1'),
    ]

    def _real_initialize(self):
        self._login()

    @staticmethod
    def _rsa_fun(data):
        # public key extracted from http://static.iqiyi.com/js/qiyiV2/20160129180840/jobs/i18n/i18nIndex.js
        N = 0xab86b6371b5318aaa1d3c9e612a9f1264f372323c8c0f19875b5fc3b3fd3afcc1e5bec527aa94bfa85bffc157e4245aebda05389a5357b75115ac94f074aefcd
        e = 65537

        return ohdave_rsa_encrypt(data, e, N)

    def _login(self):
        (username, password) = self._get_login_info()

        # No authentication to be performed
        if not username:
            return True

        data = self._download_json(
            'http://kylin.iqiyi.com/get_token', None,
            note='Get token for logging', errnote='Unable to get token for logging')
        sdk = data['sdk']
        timestamp = int(time.time())
        target = '/apis/reglogin/login.action?lang=zh_TW&area_code=null&email=%s&passwd=%s&agenttype=1&from=undefined&keeplogin=0&piccode=&fromurl=&_pos=1' % (
            username, self._rsa_fun(password.encode('utf-8')))

        interp = IqiyiSDKInterpreter(sdk)
        sign = interp.run(target, data['ip'], timestamp)

        validation_params = {
            'target': target,
            'server': 'BEA3AA1908656AABCCFF76582C4C6660',
            'token': data['token'],
            'bird_src': 'f8d91d57af224da7893dd397d52d811a',
            'sign': sign,
            'bird_t': timestamp,
        }
        validation_result = self._download_json(
            'http://kylin.iqiyi.com/validate?' + compat_urllib_parse_urlencode(validation_params), None,
            note='Validate credentials', errnote='Unable to validate credentials')

        MSG_MAP = {
            'P00107': 'please login via the web interface and enter the CAPTCHA code',
            'P00117': 'bad username or password',
        }

        code = validation_result['code']
        if code != 'A00000':
            msg = MSG_MAP.get(code)
            if not msg:
                msg = 'error %s' % code
                if validation_result.get('msg'):
                    msg += ': ' + validation_result['msg']
            self._downloader.report_warning('unable to log in: ' + msg)
            return False

        return True

    @staticmethod
    def _gen_sc(tvid, timestamp):
        M = [1732584193, -271733879]
        M.extend([~M[0], ~M[1]])
        I_table = [7, 12, 17, 22, 5, 9, 14, 20, 4, 11, 16, 23, 6, 10, 15, 21]
        C_base = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 8388608, 432]

        def L(n, t):
            if t is None:
                t = 0
            return trunc(((n >> 1) + (t >> 1) << 1) + (n & 1) + (t & 1))

        def trunc(n):
            n = n % 0x100000000
            if n > 0x7fffffff:
                n -= 0x100000000
            return n

        def transform(string, mod):
            num = int(string, 16)
            return (num >> 8 * (i % 4) & 255 ^ i % mod) << ((a & 3) << 3)

        C = list(C_base)
        o = list(M)
        k = str(timestamp - 7)
        for i in range(13):
            a = i
            C[a >> 2] |= ord(k[a]) << 8 * (a % 4)

        for i in range(16):
            a = i + 13
            start = (i >> 2) * 8
            r = '03967743b643f66763d623d637e30733'
            C[a >> 2] |= transform(''.join(reversed(r[start:start + 8])), 7)

        for i in range(16):
            a = i + 29
            start = (i >> 2) * 8
            r = '7038766939776a32776a32706b337139'
            C[a >> 2] |= transform(r[start:start + 8], 1)

        for i in range(9):
            a = i + 45
            if i < len(tvid):
                C[a >> 2] |= ord(tvid[i]) << 8 * (a % 4)

        for a in range(64):
            i = a
            I = i >> 4
            C_index = [i, 5 * i + 1, 3 * i + 5, 7 * i][I] % 16 + urshift(a, 6)
            m = L(L(o[0], [
                trunc(o[1] & o[2]) | trunc(~o[1] & o[3]),
                trunc(o[3] & o[1]) | trunc(~o[3] & o[2]),
                o[1] ^ o[2] ^ o[3],
                o[2] ^ trunc(o[1] | ~o[3])
            ][I]), L(
                trunc(int(abs(math.sin(i + 1)) * 4294967296)),
                C[C_index] if C_index < len(C) else None))
            I = I_table[4 * I + i % 4]
            o = [o[3],
                 L(o[1], trunc(trunc(m << I) | urshift(m, 32 - I))),
                 o[1],
                 o[2]]

        new_M = [L(o[0], M[0]), L(o[1], M[1]), L(o[2], M[2]), L(o[3], M[3])]
        s = [new_M[a >> 3] >> (1 ^ a & 7) * 4 & 15 for a in range(32)]
        return binascii.hexlify(intlist_to_bytes(s))[1::2].decode('ascii')

    def get_raw_data(self, tvid, video_id):
        tm = int(time.time() * 1000)

        sc = self._gen_sc(tvid, tm)
        params = {
            'platForm': 'h5',
            'rate': 1,
            'tvid': tvid,
            'vid': video_id,
            'cupid': 'qc_100001_100186',
            'type': 'mp4',
            'nolimit': 0,
            'agenttype': 13,
            'src': 'd846d0c32d664d32b6b54ea48997a589',
            'sc': sc,
            't': tm - 7,
            '__jsT': None,
        }

        headers = {}
        cn_verification_proxy = self._downloader.params.get('cn_verification_proxy')
        if cn_verification_proxy:
            headers['Ytdl-request-proxy'] = cn_verification_proxy
        return self._download_json(
            'http://cache.m.iqiyi.com/jp/tmts/%s/%s/' % (tvid, video_id),
            video_id, transform_source=lambda s: remove_start(s, 'var tvInfoJs='),
            query=params, headers=headers)

    def _extract_playlist(self, webpage):
        PAGE_SIZE = 50

        links = re.findall(
            r'<a[^>]+class="site-piclist_pic_link"[^>]+href="(http://www\.iqiyi\.com/.+\.html)"',
            webpage)
        if not links:
            return

        album_id = self._search_regex(
            r'albumId\s*:\s*(\d+),', webpage, 'album ID')
        album_title = self._search_regex(
            r'data-share-title="([^"]+)"', webpage, 'album title', fatal=False)

        entries = list(map(self.url_result, links))

        # Start from 2 because links in the first page are already on webpage
        for page_num in itertools.count(2):
            pagelist_page = self._download_webpage(
                'http://cache.video.qiyi.com/jp/avlist/%s/%d/%d/' % (album_id, page_num, PAGE_SIZE),
                album_id,
                note='Download playlist page %d' % page_num,
                errnote='Failed to download playlist page %d' % page_num)
            pagelist = self._parse_json(
                remove_start(pagelist_page, 'var tvInfoJs='), album_id)
            vlist = pagelist['data']['vlist']
            for item in vlist:
                entries.append(self.url_result(item['vurl']))
            if len(vlist) < PAGE_SIZE:
                break

        return self.playlist_result(entries, album_id, album_title)

    def _real_extract(self, url):
        webpage = self._download_webpage(
            url, 'temp_id', note='download video page')

        # There's no simple way to determine whether an URL is a playlist or not
        # So detect it
        playlist_result = self._extract_playlist(webpage)
        if playlist_result:
            return playlist_result

        tvid = self._search_regex(
            r'data-player-tvid\s*=\s*[\'"](\d+)', webpage, 'tvid')
        video_id = self._search_regex(
            r'data-player-videoid\s*=\s*[\'"]([a-f\d]+)', webpage, 'video_id')

        for _ in range(5):
            raw_data = self.get_raw_data(tvid, video_id)

            if raw_data['code'] != 'A00000':
                if raw_data['code'] == 'A00111':
                    self.raise_geo_restricted()
                raise ExtractorError('Unable to load data. Error code: ' + raw_data['code'])

            data = raw_data['data']

            # iQiYi sometimes returns Ads
            if not isinstance(data['playInfo'], dict):
                self._sleep(5, video_id)
                continue

            title = data['playInfo']['an']
            break

        return {
            'id': video_id,
            'title': title,
            'url': data['m3u'],
        }
